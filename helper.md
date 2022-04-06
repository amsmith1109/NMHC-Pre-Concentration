### Use GH CLI for git authentication ###
# First install gh
sudo apt-get install gh

# Generate a personal access token (PAT). I use the web interface.
# Then through VNC copy+pasted into a text file
# Then login using the PAT, see https://cli.github.com/manual/gh_auth_login
gh auth login --with-token < mytoken.txt

# Save credentials to git
git config --global --add 'credential.https://github.com.helper' '!gh auth git-credential'

### Get repo ###
git clone https://github.com/amsmith1109/NMHC-Pre-Concentration

### General sequence for pushing to repo ###
cd NMHC-Pre-Concentration
git add .
git commit -m "commit description"
git push main origin

