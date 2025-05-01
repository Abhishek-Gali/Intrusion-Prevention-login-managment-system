import cv2
import os
import numpy as np
import pickle
import imutils

def validate_photo(image_path):
    """Validate that the file is a valid image based on extension and size."""
    try:
        # Check file extension
        file_extension = os.path.splitext(image_path)[1].lower()
        if file_extension not in [".jpg", ".jpeg", ".png"]:
            return False, f"Invalid file type: {file_extension}. Must be .jpg, .jpeg, or .png"
        
        # Check file syize (5MB limit)
        file_size = os.path.getsize(image_path)
        if file_size > 10 * 1024 * 1024:
            return False, "File exceeds 5MB"
        
        # Optional: Basic image loading check to ensure it's a valid image
        image = cv2.imread(image_path)
        if image is None:
            return False, f"Invalid image file: {image_path}"
        
        return True, None
    except Exception as e:
        return False, f"Error validating file: {str(e)}"

def preprocess_face(face):
    if face.size == 0:
        return None
    face = cv2.resize(face, (100, 100))
    face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
    face = cv2.equalizeHist(face)
    face = cv2.cvtColor(face, cv2.COLOR_GRAY2BGR)
    return face.astype(np.float32) / 255.0

def eye_aspect_ratio(eye):
    A = np.linalg.norm(eye[1] - eye[5])
    B = np.linalg.norm(eye[2] - eye[4])
    C = np.linalg.norm(eye[0] - eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

def extract_face(image_path, net, landmark_net):
    is_valid, error_msg = validate_photo(image_path)
    if not is_valid:
        return None, error_msg

    image = cv2.imread(image_path)
    if image is None:
        return None, f"Failed to load image: {image_path}"
    
    image = imutils.resize(image, width=800)
    h, w = image.shape[:2]
    
    blob = cv2.dnn.blobFromImage(image, 1.0, (300, 300), (104, 177, 123))
    net.setInput(blob)
    detections = net.forward()
    
    if detections.shape[2] == 0:
        return None, f"No face detected in {image_path}"
    
    i = np.argmax(detections[0, 0, :, 2])
    confidence = detections[0, 0, i, 2]
    if confidence < 0.65:
        return None, f"No face detected with sufficient confidence in {image_path}"
    
    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h], dtype=np.float32)
    (startX, startY, endX, endY) = box.astype("int")
    startX, startY = max(0, startX), max(0, startY)
    endX, endY = min(w, endX), min(h, endY)
    
    expansion = int(((endX - startX) + (endY - startY)) / 20)
    startX = max(0, startX - expansion)
    startY = max(0, startY - expansion)
    endX = min(w, endX + expansion)
    endY = min(h, endY + expansion)
    
    face = image[startY:endY, startX:endX]
    if face.size == 0:
        return None, f"Empty face region in {image_path}"
    
    face_input = cv2.resize(face, (192, 192))
    face_blob = cv2.dnn.blobFromImage(face_input, 1.0 / 255.0, (192, 192), swapRB=True, crop=False)
    landmark_net.setInput(face_blob)
    preds = landmark_net.forward()
    
    landmarks = preds[0].reshape(-1, 2)
    landmarks *= np.array([face.shape[1], face.shape[0]])

    try:
        left_eye = landmarks[36:42]
        right_eye = landmarks[42:48]
        left_ear = eye_aspect_ratio(left_eye)
        right_ear = eye_aspect_ratio(right_eye)
        ear = (left_ear + right_ear) / 2.0
        if ear < 0.2:
            return None, f"Blink detected in {image_path}"
    except Exception as e:
        return None, f"Landmark detection failed in {image_path}: {str(e)}"
    
    return preprocess_face(face), None

def main():
    print("Starting face embedding extraction...")
    net = cv2.dnn.readNetFromCaffe('deploy.prototxt.txt', 'res10_300x300_ssd_iter_140000.caffemodel')
    landmark_net = cv2.dnn.readNetFromONNX("models/face_detection_yunet/face_detection_yunet_2023mar_int8.onnx")

    dataset_path = "dataset"
    if not os.path.exists(dataset_path):
        os.makedirs(dataset_path)
        print("Created dataset directory. Add person folders with images.")
        return

    known_embeddings = []
    known_names = []
    processed_count = 0
    error_count = 0

    for person_name in os.listdir(dataset_path):
        person_folder = os.path.join(dataset_path, person_name)
        if not os.path.isdir(person_folder):
            continue

        print(f"\nProcessing images for {person_name}...")
        person_processed = 0
        person_errors = 0

        for img_name in os.listdir(person_folder):
            if not img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue

            img_path = os.path.join(person_folder, img_name)
            print(f"  Processing {img_name}...", end="", flush=True)

            face, error_msg = extract_face(img_path, net, landmark_net)
            if face is None:
                print(f" Error: {error_msg}")
                person_errors += 1
                error_count += 1
                continue

            try:
                embedding = face.flatten()
                if embedding.shape != (30000,):
                    print(f" Error: Unexpected embedding shape {embedding.shape}")
                    person_errors += 1
                    error_count += 1
                    continue

                known_embeddings.append(embedding)
                known_names.append(person_name)
                print(" Done")
                processed_count += 1
                person_processed += 1

            except Exception as e:
                print(f" Error: {str(e)}")
                person_errors += 1
                error_count += 1
                continue

        print(f"Completed {person_name}: {person_processed} images processed, {person_errors} errors")

    if processed_count == 0:
        print("\nNo faces processed. Check dataset.")
        return

    print(f"\nTotal faces extracted: {processed_count}")
    print(f"Total errors: {error_count}")
    print(f"People identified: {list(set(known_names))}")

    data = {"embeddings": known_embeddings, "names": known_names}
    with open("embeddings.pickle", "wb") as f:
        pickle.dump(data, f, protocol=4)
    print("\nEmbeddings saved to embeddings.pickle")

if __name__ == "__main__":
    main()