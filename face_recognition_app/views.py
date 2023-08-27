from .models import User
import dlib
import cv2
from django.http import HttpResponse, StreamingHttpResponse
from django.shortcuts import render, redirect
from django.views.decorators import gzip
import pickle
import numpy as np
from PIL import Image
import io


face_detector = dlib.get_frontal_face_detector()
shape_predictor = dlib.shape_predictor("face_recognition_app/models/shape_predictor_68_face_landmarks.dat")
face_recognizer = dlib.face_recognition_model_v1("face_recognition_app/models/dlib_face_recognition_resnet_model_v1.dat")

def find_match(face_descriptor):
    for known_face in User.objects.all():
        known_descriptor = pickle.loads(known_face.face_descriptor)
        known_descriptor_np = np.array(known_descriptor)
        face_descriptor_np = np.array(face_descriptor)
        distance = np.linalg.norm(known_descriptor_np - face_descriptor_np)
        if distance < 0.6:
            return known_face.name
    return None

def process_frame(frame):
    faces = face_detector(frame)

    for face in faces:
        shape = shape_predictor(frame, face)  # Get facial landmarks
        face_descriptor = face_recognizer.compute_face_descriptor(frame, shape)

        match = find_match(face_descriptor)
        if match:
            label = "Known: " + match
            cv2.putText(frame, label, (face.left(), face.top() - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            cv2.rectangle(frame, (face.left(), face.top()), (face.right(), face.bottom()), (0, 255, 0), 2)
        else:
            label = "Unknown"
            cv2.putText(frame, label, (face.left(), face.top() - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            cv2.rectangle(frame, (face.left(), face.top()), (face.right(), face.bottom()), (0, 0, 255), 2)

    return frame

def generate_frames():
    camera = cv2.VideoCapture(0)
    while True:
        _, frame = camera.read()
        processed_frame = process_frame(frame)
        _, buffer = cv2.imencode('.jpg', processed_frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@gzip.gzip_page
def video_feed(request):
    return StreamingHttpResponse(generate_frames(), content_type="multipart/x-mixed-replace;boundary=frame")


def index(request):
    return render(request, 'index.html')

def add_user(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        uploaded_file = request.FILES['file']
        
        # Read the uploaded image into memory
        image_data = uploaded_file.read()
        
        # Open the image using PIL
        image = Image.open(io.BytesIO(image_data))
        
        # Convert the image to RGB format
        image = image.convert('RGB')
        
        # Convert the PIL image to a numpy array
        image_array = np.array(image)
        
        # Perform face detection
        faces = face_detector(image_array)
        
        if len(faces) == 0:
            return HttpResponse("No face found in the uploaded image")

        face = faces[0]  # Assuming you want to process the first detected face
        
        # Convert face rectangle to dlib rectangle
        dlib_rect = dlib.rectangle(face.left(), face.top(), face.right(), face.bottom())
        
        # Get facial landmarks
        shape = shape_predictor(image_array, dlib_rect)
        
        # Compute face descriptor
        face_descriptor = face_recognizer.compute_face_descriptor(image_array, shape)

        user = User(name=name, image=uploaded_file, face_descriptor=pickle.dumps(face_descriptor))
        user.save()
        
        return redirect('user_list')


def face_detection(request):
    return render(request, 'face_detection.html')

def user_list(request):
    users = User.objects.all()
    return render(request, 'users_list.html', {'users': users})

def delete_user(request, user_id):
    user = User.objects.get(pk=user_id)
    user.delete()
    return redirect('user_list')
