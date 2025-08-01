import os
from PIL import Image
from pillow_heif import register_heif_opener
from PIL.ExifTags import TAGS
from pymediainfo import MediaInfo
from datetime import datetime
from dateutil import tz
import subprocess
import json
import bpy
import math
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
        # if image_path.endswith('IMG_0219.MOV'):
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




def add_images_to_sequence_editor(folder_path):
     # Clear all existing strips from the sequence editor
    if bpy.context.scene.sequence_editor:
        for strip in reversed(bpy.context.scene.sequence_editor.sequences_all):
            bpy.context.scene.sequence_editor.sequences.remove(strip)
        print("Cleared existing sequence editor strips.")
    # Set the scene's frame rate to ensure consistent timing
    bpy.context.scene.render.fps = video_fps


    media_files = get_sorted_media_files(image_folder)
    
    current_start_frame = 1
    for i, media_obj in enumerate(media_files):
#        if i > 50:
#            break
        print(f"{media_obj['name']} , {media_obj['path']} ")

        media_duration =  img_frame_duration
        media_strip = None
        if not media_obj['is_vid']:
            # Add image strip         
            image_strip = bpy.context.scene.sequence_editor.sequences.new_image(
                name=media_obj['name'],
                filepath=media_obj['path'],
                channel=1, # Channel 1 for images
                frame_start=current_start_frame,
                fit_method='FIT'
            )
            if media_obj['orientation'] == 8:
                print(f"Rotating by 90 :{media_obj['heightx']} , {media_obj['widthx']} ")
                image_strip.transform.rotation = math.radians(90)
            media_strip = image_strip
            image_strip.frame_final_duration = img_frame_duration
        else:
            mov_strip = bpy.context.scene.sequence_editor.sequences.new_movie(
                name=media_obj['name'],
                filepath=media_obj['path'],
                channel=3, # Channel 1 for images
                frame_start=current_start_frame,
                fit_method='FIT'
            )
            if 'rotation' in media_obj and float(media_obj['rotation']) >=90 :
                print(f"Rotating video by {media_obj['rotation']} degrees: {media_obj['name']}")
                mov_strip.transform.scale_x = 2.5
                mov_strip.transform.scale_y = 2.5
                mov_strip.transform.offset_y = -225
            if float(media_obj['fps']) - video_fps > 10:
                print(f"speeding up the clip {media_obj['fps']}")
                speed_strip = bpy.context.scene.sequence_editor.sequences.new_effect(
                    name=f"MySpeedControl{i}",
                    type='SPEED',
                    channel=5,
                    frame_start=current_start_frame,
                    input1=mov_strip
                )
                speed_strip.speed_control = 'MULTIPLY'
                speed_strip.speed_factor = 2
                speed_strip.use_frame_interpolate = True # Optional: for smoother playback
                original_duration = mov_strip.frame_final_duration
                mov_strip.frame_final_end = mov_strip.frame_final_start + int(original_duration / 2)
            
            media_strip = mov_strip
            media_duration = mov_strip.frame_final_end - current_start_frame
 
        if i > 0:
            # Create a Crossfade effect strip
            fade_strip = bpy.context.scene.sequence_editor.sequences.new_effect(
                name=f"Crossfade{i}",
                type='CROSS' ,
                channel=7, # Use a higher channel for effects
                frame_start=current_start_frame - fade_duration,
                frame_end=current_start_frame + fade_duration,
                input1=prev_strip,
                input2=media_strip
            )
            
        # Update the start frame for the next image
        prev_strip = media_strip

        current_start_frame += media_duration - fade_duration # Subtract fade_duration for overlap

    print(f"Added {len(media_files)} images to the Sequence Editor.")
    # Set the scene's frame_end to the last frame of the sequence
    bpy.context.scene.frame_end = current_start_frame
     # Add sound track if provided
    if background_sound and os.path.exists(background_sound):
        print(f"Adding audio track: {background_sound}")
        bpy.context.scene.sequence_editor.sequences.new_sound(
            name="Soundtrack",
            filepath=background_sound,
            channel=9, # Channel for the audio track
            frame_start=1
        )


image_folder = r"D:\pics\north-cal\Thursday-071725" 
background_sound = r"D:\pics\north-cal\sound\fsm-team-escp-chill-hop-vol-1.mp3" 
video_fps = 30
img_frame_duration = video_fps * 4 
fade_duration = video_fps * 1

add_images_to_sequence_editor(image_folder)    