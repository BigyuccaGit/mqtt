import urequests
import os
import json
import machine

class OTAUpdater:
    
    """ This class handles OTA updates. It connects to the Wi-Fi, checks for updates, downloads and installs them."""
    def __init__(self, repo_url):
        self.repo_url = repo_url
        self.latest_version_from_repo = 0
        self.local_version_filename=""
        self.origin ="master/"
        if "www.github.com" in self.repo_url :
            print(f"Updating {repo_url} to raw.githubusercontent")
            self.repo_url = self.repo_url.replace("www.github","raw.githubusercontent")
        elif "github.com" in self.repo_url:
            print(f"Updating {repo_url} to raw.githubusercontent'")
            self.repo_url = self.repo_url.replace("github","raw.githubusercontent")            
 
        self.versions_on_repo_url = self.repo_url + self.origin + 'versions.json'

        print(f"versions url is: {self.versions_on_repo_url}")
        self.filename = ""
        self.restart_required = False
        
    def fetch_latest_code_from_repo(self)->bool:
        """ Fetch the latest code from the repo, returns False if not found."""
        
        # Fetch the latest code from the repo.
        response = urequests.get(self.filename_on_repo_url)
        if response.status_code == 200:
            print(f'Fetched latest filename code from repo, status: {response.status_code}')
    
            # Save the fetched code to memory
            self.latest_code_from_repo = response.text
            return True
        
        elif response.status_code == 404:
            print(f'Filename not found - {self.filename_on_repo_url}.')
            return False

        # Save the fetched code and update the version file to latest version.
        with open('latest_code_from_repo.py', 'w') as f:
            f.write(self.latest_code_from_repo)
        
        # update the version in memory
        self.current_version_in_memory = self.latest_version_from_repo

        # save the current version
        print("local_version_filename", self.local_version_filename)
        with open(self.local_version_filename, 'w') as f:
            json.dump({'version': self.current_version_in_memory}, f)
        
        # free up some memory
        self.latest_code_from_repo = None

    def update_code(self):
        """ Update the code """

        print(f"Updating device... (Renaming 'latest_code_from_repo.py' to '{self.filename}')")

        # Overwrite the old code.
        os.rename('latest_code_from_repo.py', self.filename)
        self.restart_required = True

    def save_code_and_update_version_file(self):

        # Save the fetched code and update the version file to latest version.
        with open('latest_code_from_repo.py', 'w') as f:
            f.write(self.latest_code_from_repo)
        
        # update the version in memory
        self.current_version_in_memory = self.latest_version_from_repo

        # save the current version
        print(f"Updating local_version_filename: '{self.local_version_filename}'")
        with open(self.local_version_filename, 'w') as f:
            json.dump({'version': self.current_version_in_memory}, f)
        
        # free up some memory
        self.latest_code_from_repo = None
        
    def check_for_updates(self):
        """ Check if updates are available."""
        
        print(f'Checking for latest version... on {self.version_on_repo_url}')
        response = urequests.get(self.version_on_repo_url)
 
        data = json.loads(response.text)
        
        self.latest_version_from_repo = int(data['version'])
        print(f'latest version is: {self.latest_version_from_repo}')
     
        # compare versions
        newer_version_available = True if self.current_version_in_memory < self.latest_version_from_repo else False
        
        print(f'Newer version available: {newer_version_available}')    
        return newer_version_available
 
    def ordered_list_of_files_and_versions(self):
        print(f'Checking for latest versions... on {self.versions_on_repo_url}')
        response = urequests.get(self.versions_on_repo_url)
 
        data2 = json.loads(response.text)
        
        # Store data in list
        l=[k for k in data2]
        # place main.py at end of list
        l.sort(key=lambda f:0 if f != "main.py" else 1)
        
 #       Derive ordered list of (filename, version) tuples
        lfv=[]
        for filename in l:
            lfv.append((filename,int(data2[filename])))
            
        return lfv
    
    def newer_version(self, filename, version):
        self.filename = filename
        self.latest_version_from_repo = version
        print("")
        print(f"Filename = '{filename}', version = {self.latest_version_from_repo}")
        self.filename_on_repo_url = self.repo_url + self.origin + filename
        print(f"Remote file is {self.filename_on_repo_url}")
        self.local_version_filename = filename + ".version.json"
        print(f"Local version file is : {self.local_version_filename}")
        
        if self.local_version_filename in os.listdir():    
            with open(self.local_version_filename) as f:
                self.current_version_in_memory = int(json.load(f)['version'])
            print(f"Current device filename version is '{self.current_version_in_memory}'")

        else:
            self.current_version_in_memory = 0
            # save the current version
            with open(self.local_version_filename, 'w') as f:
                print(f"Writing default local version file : {self.local_version_filename}")
                json.dump({'version': self.current_version_in_memory}, f)
                
        # compare versions
        newer_version_available = True if self.current_version_in_memory < self.latest_version_from_repo else False
    
        if newer_version_available :
            print(f'Newer version of \'{filename}\' available')
        else:
            print(f'No newer version of \'{filename}\' available')
        
        return newer_version_available
            
    def loop_over_updates(self):

        for filename, version in self.ordered_list_of_files_and_versions():
            if self.newer_version(filename, version):
                if self.fetch_latest_code_from_repo():
                    self.save_code_and_update_version_file() 
                    self.update_code() 
 #           else:
 #               print(f" update available for '{filename}'.")
                
        if self.restart_required:
            print("Restarting...")
    #       machine.reset()  # Reset the device to run the new code.
                    
                    