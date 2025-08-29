import os
import pyzipper

def zip_folder_with_password(folder_path, zip_path, password, include_subfolders=False):
    """
    Zips all files in folder_path (optionally including subfolders), password-protected.
    
    Args:
        folder_path (str): Path to the directory to zip.
        zip_path (str): Output path for the zip file.
        password (str): Password for the zip file.
        include_subfolders (bool): If True, include files from subfolders. Default is False (top-level only).
        
    Returns:
        str: Status message.
    """
    password_bytes = password.encode('utf-8')
    with pyzipper.AESZipFile(zip_path, 'w', compression=pyzipper.ZIP_LZMA, encryption=pyzipper.WZ_AES) as zf:
        zf.pwd = password_bytes
        if include_subfolders:
            # Walk through all directories and subdirectories
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    absfn = os.path.join(root, file)
                    arcname = os.path.relpath(absfn, folder_path)
                    zf.write(absfn, arcname)
        else:
            # Only include files in the top-level directory
            for file in os.listdir(folder_path):
                absfn = os.path.join(folder_path, file)
                if os.path.isfile(absfn):
                    zf.write(absfn, file)
    return f"Created {zip_path} with password protection. Include subfolders: {include_subfolders}"