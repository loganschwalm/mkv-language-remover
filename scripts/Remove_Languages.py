import os
import subprocess
import orjson

# Set the base directory to the movies folder
base_dir = '/movies'

def get_exclusion_track_ids(data):
    exclusion_ids = {"audio": [], "subtitles": []}
    excluded_languages = ["rus", "ukr", "kaz"]

    audio_languages = set()
    subtitle_languages = set()

    commentary_audio_exists = False

    for track in data.get("tracks", []):
        track_type = track["type"]
        track_language = track["properties"].get("language")
        track_name = track["properties"].get("track_name", "").lower()

        # Check for audio tracks named "Commentary"
        if track_type == "audio" and "commentary" in track_name:
            commentary_audio_exists = True
            exclusion_ids[track_type].append(str(track["id"]))

        if track_type == "audio":
            audio_languages.add(track_language)
            if track_language in excluded_languages:
                exclusion_ids["audio"].append(str(track["id"]))
        elif track_type == "subtitles":
            subtitle_languages.add(track_language)
            if (
                track_language in excluded_languages
                and track_language in audio_languages
            ):
                exclusion_ids["subtitles"].append(str(track["id"]))

            # Add commentary subtitles to exclusion only if the corresponding audio exists
            if "commentary" in track_name and commentary_audio_exists:
                exclusion_ids["subtitles"].append(str(track["id"]))

    # Prevent exclusion if it's the only language available
    for lang in excluded_languages:
        if audio_languages == {lang}:
            exclusion_ids["audio"] = [
                track_id
                for track_id in exclusion_ids["audio"]
                if track_id
                not in [
                    str(t["id"])
                    for t in data.get("tracks", [])
                    if t["properties"].get("language") == lang
                ]
            ]
        if subtitle_languages == {lang}:
            exclusion_ids["subtitles"] = [
                track_id
                for track_id in exclusion_ids["subtitles"]
                if track_id
                not in [
                    str(t["id"])
                    for t in data.get("tracks", [])
                    if t["properties"].get("language") == lang
                ]
            ]

    return exclusion_ids

movie_count = 0
total_movies = 0

# Iterate over each subdirectory in the base directory
for subdir, dirs, files in os.walk(base_dir):
    for file in files:
        # Check if the file is an MKV file
        if file.endswith(".mkv"):
            total_movies += 1

# Iterate over each subdirectory in the base directory
for subdir, dirs, files in os.walk(base_dir):
    for file in files:
        if movie_count >= total_movies:
            print("Processed all movies. Stopping further processing.")
            break

        # Check if the file is an MKV file
        if file.endswith(".mkv"):
            filepath = os.path.join(subdir, file)
            temp_filepath = os.path.join(subdir, "temp_" + file)

            # Run mkvmerge -J to get the JSON output
            result = subprocess.run(
                ["mkvmerge", "-J", filepath], capture_output=True, text=True
            )

            if result.returncode != 0:
                print(f"Error running mkvmerge for {filepath}: {result.stderr}")
                continue

            try:
                # Parse the JSON content
                data = orjson.loads(result.stdout)

                # Ensure 'tracks' key exists in JSON before proceeding
                if "tracks" not in data:
                    print(f"No track information found in {filepath}.")
                    continue

                exclusion_ids = get_exclusion_track_ids(data)

                if exclusion_ids["audio"] or exclusion_ids["subtitles"]:
                    movie_count += 1
                    print(f"\nProcessing movie {movie_count} of {total_movies}: {filepath}")

                    for track_id in exclusion_ids["audio"]:
                        print(f"Removing audio track number {track_id}...")

                    for track_id in exclusion_ids["subtitles"]:
                        print(f"Removing subtitle track number {track_id}...")

                    # Constructing the mkvmerge command
                    mkvmerge_command = ["mkvmerge", "-o", temp_filepath]

                    if exclusion_ids["audio"]:
                        excluded_audio = "!" + ",".join(exclusion_ids["audio"])
                        mkvmerge_command.extend(["-a", excluded_audio])

                    if exclusion_ids["subtitles"]:
                        excluded_subtitles = "!" + ",".join(exclusion_ids["subtitles"])
                        mkvmerge_command.extend(["-s", excluded_subtitles])

                    mkvmerge_command.append(filepath)

                    # Run the mkvmerge command with output suppression
                    with open(os.devnull, "w") as null:
                        result = subprocess.run(
                            mkvmerge_command, stdout=null, stderr=null
                        )

                    # If the remux process is successful, remove the original file and rename the new one
                    if result.returncode == 0:
                        os.remove(filepath)
                        os.rename(temp_filepath, filepath)
                    else:
                        print(
                            f"Error processing {filepath}. Keeping the original file."
                        )

            except orjson.JSONDecodeError:
                print(f"Failed to decode JSON output for {filepath}.")
            except KeyError as e:
                print(
                    f"KeyError {e} when processing {filepath}, this file may have an unexpected structure."
                )
