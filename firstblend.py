import bpy
import mediasorter


def add_images_to_sequence_editor(folder_path):
    
    # Set the scene's frame rate to ensure consistent timing
    bpy.context.scene.render.fps = video_fps

    # Clear existing VSE strips (optional, uncomment if you want to start fresh)
    bpy.ops.sequencer.delete_all_strips()

    media_files = mediasorter.get_sorted_media_files(image_folder)
    
    current_start_frame = 1
    for i, media_obj in enumerate(media_files):
        if i > 20:
            break

        # Add image strip         
        image_strip = bpy.context.scene.sequence_editor.sequences.new_image(
            name=media_obj['name'],
            filepath=media_obj['path'],
            channel=1, # Channel 1 for images
            frame_start=current_start_frame,
            fit_method='FIT'
        )
        image_strip.frame_final_duration = img_frame_duration
 
        if i > 0:

            # Create a Crossfade effect strip
            fade_strip = bpy.context.scene.sequence_editor.sequences.new_effect(
                name=f"Crossfade{i}",
                type='CROSS' ,
                channel=3, # Use a higher channel for effects
                frame_start=current_start_frame - fade_duration,
                frame_end=current_start_frame + fade_duration,
                input1=prev_strip,
                input2=image_strip
            )
            
        # Update the start frame for the next image
        prev_strip = image_strip

        if not media_obj['is_vid']:
            print('break')

        current_start_frame += img_frame_duration - fade_duration # Subtract fade_duration for overlap

    print(f"Added {len(media_files)} images to the Sequence Editor.")


image_folder = r"D:\pics\north-cal\redwood" 
video_fps = 25
img_frame_duration = video_fps * 4 
fade_duration = video_fps * 1

add_images_to_sequence_editor(image_folder)