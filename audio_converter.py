import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account
import ffmpeg

def download_wav_from_google_drive(google_drive_folder_id, output_folder):
    credentials = service_account.Credentials.from_service_account_file('service_account_key.json')
    service = build('drive', 'v3', credentials=credentials)

    query = f"'{google_drive_folder_id}' in parents and mimeType = 'audio/wav' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for file in files:
        file_id = file['id']
        file_name = file['name']
        wav_path = os.path.join(output_folder, file_name)

        request = service.files().get_media(fileId=file_id)
        fh = MediaFileUpload(wav_path, mimetype='audio/wav', resumable=True)

        print(f"Downloading: {file_name}")
        with open(wav_path, 'wb') as f:
            downloader = MediaFileDownload(request, f)
            done = False
            while done is False:
                status, done = downloader.next_chunk()

    print("Download completed.")

def convert_wav_to_mp3(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for root, _, files in os.walk(input_folder):
        for filename in files:
            if filename.lower().endswith('.wav'):
                wav_path = os.path.join(root, filename)
                mp3_filename = os.path.splitext(filename)[0] + '.mp3'
                mp3_path = os.path.join(output_folder, mp3_filename)

                print(f"Converting: {wav_path} -> {mp3_path}")

                ffmpeg.input(wav_path).output(mp3_path, acodec='libmp3lame').run()

    print("Conversion completed.")

def upload_to_google_drive(mp3_folder, google_drive_folder_id):
    credentials = service_account.Credentials.from_service_account_file('service_account_key.json')
    service = build('drive', 'v3', credentials=credentials)

    for root, _, files in os.walk(mp3_folder):
        for filename in files:
            mp3_path = os.path.join(root, filename)

            # Update the file name to include the full path to the MP3 file
            mp3_full_path = os.path.join(mp3_folder, mp3_path)

            print(f"Uploading: {mp3_full_path} to Google Drive")

            file_metadata = {
                'name': filename,
                'parents': [google_drive_folder_id],
            }

            media = MediaFileUpload(mp3_full_path, resumable=True)

            service.files().create(body=file_metadata, media_body=media).execute()

    print("Upload to Google Drive completed.")

if __name__ == "__main__":
    google_drive_folder_id = "1R03Me1zw4g6r7er3W1xfhldHQAE_v2VP"  # Replace with the ID of the source folder on Google Drive
    output_folder = "/path/to/temporary/folder"  # Replace with the path to a temporary folder on your local system

    download_wav_from_google_drive(google_drive_folder_id, output_folder)

    convert_wav_to_mp3(output_folder, output_folder)

    upload_to_google_drive(output_folder, google_drive_folder_id)