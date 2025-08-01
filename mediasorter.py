import os
from PIL import Image
from pillow_heif import register_heif_opener
from PIL.ExifTags import TAGS
from pymediainfo import MediaInfo
from datetime import datetime
from dateutil import tz
import subprocess
import json


# Register HEIC opener
register_heif_opener()

utc_date_time_format_string = "%Y-%m-%d %H:%M:%S UTC"
utc_date_time_format_string2 = "%Y-%m-%d %H:%M:%S.%f UTC"
utc_date_time_format_string3 = "%Y:%m:%d %H:%M:%S"

def convert_heic_to_jpg(heic_path):
    base_name = os.path.splitext(os.path.basename(heic_path))[0]
    jpg_path = os.path.join(os.path.dirname(heic_path)+"\heic", f"{base_name}.jpg")
    if os.path.exists( jpg_path):
        return jpg_path
    img = Image.open(heic_path)
    rgb_img = img.convert('RGB')
    os.makedirs(os.path.dirname(heic_path)+"\heic", exist_ok=True)
    rgb_img.save(jpg_path, "jpeg")
    print(f"Successfully converted '{heic_path}' to '{jpg_path}'")
    return jpg_path
        
def get_exif_data(image_path):
    """Extracts EXIF data from an image file."""
    try:
        img = Image.open(image_path)
        exif_data = img._getexif()
        if exif_data is not None:
            decoded_exif = {}
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, tag_id)
                decoded_exif[tag_name] = value
            decoded_exif['widthx'], decoded_exif['heightx'] = img.size 
            return decoded_exif
    except Exception as e:
        print(f"Error reading EXIF from {image_path}: {e}")
    return None

def get_img_date_taken(image_path):
    """Retrieves the 'DateTimeOriginal' from EXIF data."""
    # if image_path.endswith('PXL_20250717_231347155_exported_5950~2.jpg'):
    #         print("break")
    exif = get_exif_data(image_path)
    if exif and 'DateTimeOriginal' in exif:
        datetime_object = datetime.strptime( exif['DateTimeOriginal'], utc_date_time_format_string3)
        time_taken =   datetime_object.replace(tzinfo=tz.gettz('America/Los_Angeles'))
        img_meta = {}
        img_meta['widthx'] = exif['widthx']
        img_meta['heightx'] = exif['heightx']
        img_meta['orientation'] = exif['Orientation']
        img_meta['taken_date'] = time_taken
        return img_meta
    return None
 
def get_heic_date_taken(heic_filepath):
    """Retrieves the 'DateTimeOriginal' from EXIF data."""
    cmd = ["exiftool", "-j", "-DateTimeOriginal", "-ImageHeight","-ImageWidth","-Orientation" ,"-n" ,heic_filepath]
    output = subprocess.check_output(cmd).decode("utf-8")
    metadata = json.loads(output)
    if metadata and metadata[0].get('DateTimeOriginal'):
        datetime_object = datetime.strptime(metadata[0]['DateTimeOriginal'], utc_date_time_format_string3)
        time_taken = datetime_object.replace(tzinfo=tz.gettz('America/Los_Angeles'))
        img_meta = {}
        img_meta['widthx'] = metadata[0]['ImageWidth']
        img_meta['heightx'] = metadata[0]['ImageHeight']
        img_meta['orientation'] = metadata[0]['Orientation']
        img_meta['taken_date'] = time_taken
        return img_meta
    return None

def get_vid_date_taken(image_path):
    """Retrieves the 'DateTimeOriginal' from EXIF data."""
    media_info = MediaInfo.parse(image_path)
    vid_meta = {}
    for track in media_info.tracks:
        # if image_path.endswith('PXL_20250717_231347155~2.mp4'):
        #     print("break")
       
        if track.track_type == "Video":
            vid_meta['fps'] = track.frame_rate
            vid_meta['rotation'] = track.rotation
        if track.track_type == "General":
            #comapplequicktimecreationdate = '2025-07-15T11:29:46-0700'
            if hasattr(track, 'comapplequicktimecreationdate') and track.comapplequicktimecreationdate is not None:
                datetime_object = datetime.fromisoformat(track.comapplequicktimecreationdate)
            elif hasattr(track, 'recorded_date') and track.recorded_date is not None:
                datetime_object = datetime.strptime(track.recorded_date, utc_date_time_format_string)
                datetime_object = datetime_object.replace(tzinfo=tz.gettz('UTC'))
            elif hasattr(track, 'encoded_date') and track.encoded_date is not None:
                datetime_object = datetime.strptime(track.encoded_date, utc_date_time_format_string)
                if image_path.find("PXL_") != -1:
                    datetime_object = datetime_object.replace(tzinfo=tz.gettz('UTC'))
            elif hasattr(track, 'tagged_date') and track.tagged_date is not None:
                datetime_object = datetime.strptime(track.tagged_date, utc_date_time_format_string)
                datetime_object = datetime_object.replace(tzinfo=tz.gettz('UTC'))
            else:             
                datetime_object = datetime.strptime(track.file_creation_date , utc_date_time_format_string2)
                datetime_object = datetime_object.replace(tzinfo=tz.gettz('UTC'))
            vid_meta['taken_date'] = datetime_object.astimezone(tz.gettz('America/Los_Angeles'))
    return vid_meta


def get_sorted_media_files(folder_path):
     
    image_files = []
    for f in os.listdir(folder_path):
        full_path = os.path.join(folder_path, f)
        if not os.path.isfile(full_path ):
            continue
        # Check for common image file extensions
        image_file = {}
        image_file['path'] = os.path.join(folder_path, f)
        image_file['name'] = f
        if f.lower().endswith(('.mov','mp4')):
            image_file['is_vid'] = True
            image_file.update(get_vid_date_taken(image_file['path'] ))
        
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')):
            image_file['is_vid'] = False
            image_file.update(get_img_date_taken(image_file['path'] )) 

        if f.lower().endswith(('heic')):
            image_file['is_vid'] = False
            image_file.update(get_heic_date_taken(image_file['path'] )) 
            image_file['path'] = convert_heic_to_jpg(image_file['path'])                             
        
        if 'taken_date' in image_file :
            image_files.append(image_file)
    
    
    sorted_imgs_by_time_created = sorted(image_files, key=lambda p: p['taken_date'])

    return sorted_imgs_by_time_created 

image_folder = r"D:\pics\north-cal\Thursday-071725" 
media_files = get_sorted_media_files(image_folder)
for i, media_obj in enumerate(media_files):
#        if i > 50:
#            break
        print(f"{media_obj['name']} , {media_obj['taken_date']} ")