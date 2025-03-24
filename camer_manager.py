import customtkinter as ctk
import cv2
from PIL import Image, ImageTk
import threading
import time
import os
from datetime import datetime
from tkinter import messagebox

class CameraManager(ctk.CTkToplevel):
    def __init__(self, root_window, parent_ui, playlist_manager, language_manager):
        # Initialize parent class first
        super().__init__()
        
        # Store references
        self.root = root_window
        self.parent_ui = parent_ui
        self.playlist_manager = playlist_manager
        self.language_manager = language_manager
        
        # Set temp directory path in Data folder using path_utils
        from path_utils import get_temp_image_directory
        self.temp_dir = get_temp_image_directory()
        
        # Initialize variables
        self.cap = None
        self.is_running = False
        self.capture_timer = 3
        self.current_image_path = None
        self.camera_thread = None
        self.countdown_thread = None
        
        # Ensure temp directory exists
        self._ensure_temp_directory()
        
        # Configure window
        self._setup_window()
        
        # Initialize camera
        self.initialize_camera()
        
    def _ensure_temp_directory(self):
        """Ensure temp directory exists"""
        try:
            if not os.path.exists(self.temp_dir):
                os.makedirs(self.temp_dir)
                print(f"Created temp directory at {self.temp_dir}")
        except Exception as e:
            print(f"Error creating temp directory: {e}")
            messagebox.showerror("Error", f"Could not create temp directory: {e}")
            self.destroy()
            
    def _setup_window(self):
        """Setup window properties and UI elements"""
        try:
            # Configure window
            self.title(self.language_manager.get_text("emotion_detection"))
            self.geometry("640x520")
            self.resizable(False, False)
            
            # Create main frame
            self.main_frame = ctk.CTkFrame(self)
            self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)
            
            # Create camera frame
            self.camera_frame = ctk.CTkFrame(self.main_frame)
            self.camera_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            
            # Create camera label
            self.camera_label = ctk.CTkLabel(self.camera_frame, text="")
            self.camera_label.pack(fill="both", expand=True)
            
            # Create timer label
            self.timer_label = ctk.CTkLabel(
                self.main_frame,
                text="",
                font=("Helvetica", 24, "bold")
            )
            self.timer_label.pack(pady=5)
            
            # Make window modal
            self.transient(self.root)
            self.grab_set()
            
            # Center window
            self.center_window()
            
            # Bind window close event
            self.protocol("WM_DELETE_WINDOW", self.on_closing)
            
        except Exception as e:
            print(f"Error setting up window: {e}")
            messagebox.showerror("Error", f"Could not setup window: {e}")
            self.destroy()
            
    def center_window(self):
        """Center window on screen"""
        try:
            self.update_idletasks()
            width = self.winfo_width()
            height = self.winfo_height()
            x = (self.root.winfo_screenwidth() // 2) - (width // 2)
            y = (self.root.winfo_screenheight() // 2) - (height // 2)
            self.geometry(f'{width}x{height}+{x}+{y}')
        except Exception as e:
            print(f"Error centering window: {e}")
            
    def initialize_camera(self):
        """Initialize the camera capture"""
        try:
            # Initialize camera
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise Exception("Could not open camera")
                
            # Set camera resolution
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            # Start camera thread
            self.is_running = True
            self.camera_thread = threading.Thread(target=self.update_camera)
            self.camera_thread.daemon = True
            self.camera_thread.start()
            
            # Start countdown
            self.countdown_thread = threading.Thread(target=self.start_countdown)
            self.countdown_thread.daemon = True
            self.countdown_thread.start()
            
        except Exception as e:
            print(f"Error initializing camera: {e}")
            messagebox.showerror("Error", f"Could not initialize camera: {e}")
            self.destroy()
            
    def update_camera(self):
        """Update camera feed"""
        while self.is_running:
            try:
                if self.cap is None or not self.cap.isOpened():
                    break
                    
                ret, frame = self.cap.read()
                if not ret:
                    break
                    
                # Convert frame to RGB for display
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Convert to PIL Image
                image = Image.fromarray(frame)
                
                # Resize to fit window
                image = image.resize((600, 400), Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(image=image)
                
                # Update label
                self.camera_label.configure(image=photo)
                self.camera_label.image = photo
                
                # Small delay to reduce CPU usage
                time.sleep(0.03)
                
            except Exception as e:
                print(f"Error updating camera: {e}")
                break
                
        # Cleanup
        self.cleanup_camera()
        
    def start_countdown(self):
        """Start countdown timer"""
        try:
            for i in range(self.capture_timer, 0, -1):
                if not self.is_running:
                    break
                self.timer_label.configure(text=str(i))
                time.sleep(1)
                
            if self.is_running:
                self.capture_image()
                
        except Exception as e:
            print(f"Error in countdown: {e}")
            self.cleanup_camera()
            
    def capture_image(self):
        """Capture and save image"""
        try:
            if self.cap is None or not self.cap.isOpened():
                raise Exception("Camera not initialized")
                
            # Capture frame
            ret, frame = self.cap.read()
            if not ret:
                raise Exception("Could not capture image")
                
            # Use fixed filename 'Image1.jpg' as required
            self.current_image_path = os.path.join(self.temp_dir, "Image1.jpg")
            
            # Ensure directory exists before saving
            os.makedirs(os.path.dirname(self.current_image_path), exist_ok=True)
            
            # Save image
            success = cv2.imwrite(self.current_image_path, frame)
            if not success:
                raise Exception(f"Failed to save image to: {self.current_image_path}")
            print(f"Successfully saved image to: {self.current_image_path}")
            
            # Update UI
            self.timer_label.configure(text=self.language_manager.get_text("processing"))
            
            # Process image after delay
            self.after(3000, self.process_captured_image)
            
        except Exception as e:
            print(f"Error capturing image: {e}")
            messagebox.showerror("Error", str(e))
            self.cleanup_camera()
            
    def process_captured_image(self):
        """Process captured image and cleanup"""
        try:
            if self.current_image_path and os.path.exists(self.current_image_path):
                # Process image
                self.parent_ui.process_captured_image(self.current_image_path)
            
        except Exception as e:
            print(f"Error processing image: {e}")
            messagebox.showerror("Error", str(e))
            
        finally:
            # Cleanup and close
            self.cleanup_camera()
            
    def cleanup_camera(self):
        """Clean up camera resources"""
        try:
            # Stop camera thread
            self.is_running = False
            
            # Release camera
            if self.cap is not None:
                self.cap.release()
                self.cap = None
                
            # Destroy window if it exists
            try:
                self.destroy()
            except:
                pass
                
        except Exception as e:
            print(f"Error cleaning up camera: {e}")
            
    def on_closing(self):
        """Handle window close event"""
        self.cleanup_camera()