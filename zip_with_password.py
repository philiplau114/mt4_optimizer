import os
import pyzipper
import sys
import json

def zip_folder_with_password(folder_path, zip_path, password, include_subfolders=False, remove_originals=False):
    password_bytes = password.encode('utf-8')
    files_zipped = []

    with pyzipper.AESZipFile(zip_path, 'w', compression=pyzipper.ZIP_LZMA, encryption=pyzipper.WZ_AES) as zf:
        zf.pwd = password_bytes
        if include_subfolders:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    absfn = os.path.join(root, file)
                    arcname = os.path.relpath(absfn, folder_path)
                    # Skip zip file itself
                    if os.path.abspath(absfn) != os.path.abspath(zip_path):
                        zf.write(absfn, arcname)
                        files_zipped.append(absfn)
        else:
            for file in os.listdir(folder_path):
                absfn = os.path.join(folder_path, file)
                # Skip zip file itself
                if os.path.isfile(absfn) and os.path.abspath(absfn) != os.path.abspath(zip_path):
                    zf.write(absfn, file)
                    files_zipped.append(absfn)

    # Remove originals if requested
    removed = []
    if remove_originals:
        for f in files_zipped:
            try:
                os.remove(f)
                removed.append(f)
            except Exception as e:
                print(f"Failed to remove {f}: {e}")

    msg = f"Created {zip_path} with password protection. Include subfolders: {include_subfolders}"
    if remove_originals:
        msg += f"\nRemoved {len(removed)} files:\n" + "\n".join(removed)
    return msg

if __name__ == "__main__":
    output = {}
    try:
        # Usage: python zip_with_password.py <folder_path> <zip_path> <password> [include_subfolders] [remove_originals]
        if len(sys.argv) < 4:
            output["success"] = False
            output["error"] = "Usage: python zip_with_password.py <folder_path> <zip_path> <password> [include_subfolders] [remove_originals]"
            print(json.dumps(output))
            sys.exit(1)

        folder_path = sys.argv[1]
        zip_path = sys.argv[2]
        password = sys.argv[3]
        include_subfolders = False
        remove_originals = False
        if len(sys.argv) > 4:
            include_subfolders = sys.argv[4].lower() in ['true', '1', 'yes']
        if len(sys.argv) > 5:
            remove_originals = sys.argv[5].lower() in ['true', '1', 'yes']

        msg = zip_folder_with_password(folder_path, zip_path, password, include_subfolders, remove_originals)
        output["success"] = True
        output["error"] = ""
        output["zip_path"] = zip_path
        output["message"] = msg
    except Exception as e:
        output["success"] = False
        output["error"] = str(e)
    print(json.dumps(output))