import urequests
import os
import json
import machine

class OTAUpdater:
    
    """ This class handles OTA updates. It connects to the Wi-Fi, checks for updates, downloads and installs them."""
    def __init__(self, repo_url, filename):
        self.filename = filename
        self.repo_url = repo_url
        self.origin ="master/"
        if "www.github.com" in self.repo_url :
            print(f"Updating {repo_url} to raw.githubusercontent")
            self.repo_url = self.repo_url.replace("www.github","raw.githubusercontent")
        elif "github.com" in self.repo_url:
            print(f"Updating {repo_url} to raw.githubusercontent'")
            self.repo_url = self.repo_url.replace("github","raw.githubusercontent")            
        self.version_on_repo_url = self.repo_url + self.origin + 'version.json'
        self.versions_on_repo_url = self.repo_url + self.origin + 'versions.json'
        print(f"version url is: {self.version_on_repo_url}")
        print(f"versions url is: {self.versions_on_repo_url}")
        self.filename_on_repo_url = self.repo_url + self.origin + filename

        # get the current version (stored in version.json) in memory
        if 'version.json' in os.listdir():    
            with open('version.json') as f:
                self.current_version_in_memory = int(json.load(f)['version'])
            print(f"Current device filename version is '{self.current_version_in_memory}'")

        else:
            self.current_version_in_memory = 0
            # save the current version
            with open('version.json', 'w') as f:
                json.dump({'version': self.current_version_in_memory}, f)
        
    def fetch_latest_code_from_repo(self)->bool:
        """ Fetch the latest code from the repo, returns False if not found."""
        
        # Fetch the latest code from the repo.
        response = urequests.get(self.filename_on_repo_url)
        if response.status_code == 200:
            print(f'Fetched latest filename code from repo, status: {response.status_code}, -  {response.text}')
    
            # Save the fetched code to memory
            self.latest_code_from_repo = response.text
            return True
        
        elif response.status_code == 404:
            print(f'Filename not found - {self.filename_on_repo_url}.')
            return False

    def update_no_reset(self):
        """ Update the code without resetting the device."""

        # Save the fetched code and update the version file to latest version.
        with open('latest_code_from_repo.py', 'w') as f:
            f.write(self.latest_code_from_repo)
        
        # update the version in memory
        self.current_version_in_memory = self.latest_version_from_repo

        # save the current version
        with open('version.json', 'w') as f:
            json.dump({'version': self.current_version_in_memory}, f)
        
        # free up some memory
        self.latest_code_from_repo = None

        # Overwrite the old code.
#         os.rename('latest_code_from_repo.py', self.filename)

    def update_and_reset(self):
        """ Update the code and reset the device."""

        print(f"Updating device... (Renaming latest_code_from_repo.py to {self.filename})", end="")

        # Overwrite the old code.
        os.rename('latest_code_from_repo.py', self.filename)  

        # Restart the device to run the new code.
        print('Restarting device...')
        machine.reset()  # Reset the device to run the new code.
        
    def check_for_updates(self):
        """ Check if updates are available."""
####
        print(f'Checking for latest version... on {self.version_on_repo_url}')
        response = urequests.get(self.version_on_repo_url)
        print(response.text)
        data = json.loads(response.text)
        
        print(f"data is: {data}, url is: {self.version_on_repo_url}")
        print(f"data version is: {data['version']}")
        # Turn list to dict using dictionary comprehension
#         my_dict = {data[i]: data[i + 1] for i in range(0, len(data), 2)}
        
        self.latest_version_from_repo = int(data['version'])
        print(f'latest version is: {self.latest_version_from_repo}')
####
        
####
        print(f'Checking for latest versions... on {self.versions_on_repo_url}')
        response = urequests.get(self.versions_on_repo_url)
        print(response.text)
        data2 = json.loads(response.text)
        
        print(f"data is: {data2}, url is: {self.versions_on_repo_url}")
        
        l=[k for k in data2]
        # place main.py at end of list
        l.sort(key=lambda f:0 if f != "main.py" else 1)
        print(f"data version is: {l}")
        for k in l:
            print(f"{k} : {data2[k]}")
        # Turn list to dict using dictionary comprehension
#         my_dict = {data[i]: data[i + 1] for i in range(0, len(data), 2)}
        
#        self.latest_version_from_repo = int(data['version'])
#		print(f'latest version is: {self.latest_version_from_repo}')
####            
        # compare versions
        newer_version_available = True if self.current_version_in_memory < self.latest_version_from_repo else False
        
        print(f'Newer version available: {newer_version_available}')    
        return newer_version_available
    
    def download_and_install_update_if_available(self):
        """ Check for updates, download and install them."""
        if self.check_for_updates():
            if self.fetch_latest_code_from_repo():
                self.update_no_reset() 
                self.update_and_reset() 
        else:
            print('No new updates available.')