import zipfile
import os
import logging
import shutil

class SystemMigrate:
    def __init__(self, db, platform_info):
        self.db = db
        self.platform_info = platform_info

    def export_system_config(self) -> str:
        '''
        export all system data to zip file
        '''

        platform_name = self.platform_info['PLATFORM_NAME']
        platform_version = self.platform_info['BUILD_VERSION']
        zip_location = os.path.join('/tmp', f'{platform_name}_{platform_version}.zip')

        with zipfile.ZipFile(zip_location, 'w', zipfile.ZIP_DEFLATED) as zipf:
            self._save_folder(zipf, './resources')
            self._save_folder(zipf, './data')   

        logging.warn('export system config done.')
        return zip_location

    def _save_folder(self, zipf, folder_path):
        folder_name = os.path.basename(os.path.normpath(folder_path))
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.join(folder_name,os.path.relpath(file_path, folder_path))
                zipf.write(file_path, arcname)

    def import_system_config(self, zip_file_path):
        '''
        use zip file to import system data
        '''
        success = False
        try:
            if self.db:
                self.db.stop_connection()
            extracted_path = os.path.join('/tmp', zip_file_path)
            max_uncompressed_size = 500 * 1024 * 1024  # 500MB
            total_uncompressed_size = 0

            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                for info in zip_ref.infolist():
                    total_uncompressed_size += info.file_size
                if total_uncompressed_size > max_uncompressed_size:
                    raise Exception('import system config error','compressed size too large!')
                zip_ref.extractall(extracted_path)

            extract_data_folder = os.path.join(extracted_path, 'data')
            extract_resources_folder = os.path.join(extracted_path, 'resources')

            # check zip file
            if not os.path.exists(extract_data_folder):
                shutil.rmtree(extracted_path)
                raise Exception('import system config error','necessory data folder not found in zip file!')          
                
            # check passed, start migration
            shutil.rmtree('./data')
            shutil.copytree(extract_data_folder, './data')
            if os.path.exists(extract_resources_folder): # check have resources or not
                shutil.rmtree('./resources')
                shutil.copytree(extract_resources_folder, './resources')
            shutil.rmtree(extracted_path)

            logging.warn('import system config done.')
            success = True

        except Exception as e:
            logging.error('import system config error',e)

        finally:
            if self.db:
                self.db.restart_connection()
            os.remove(zip_file_path)
        
        return success

if __name__ == '__main__':
    # before migration, run stop.sh first.
    sm = SystemMigrate(db=None, platform_info=None)
    sm.import_system_config('migrate.zip')