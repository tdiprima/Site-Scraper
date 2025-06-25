# Install Firefox and geckodriver
sudo dnf install firefox
pip install selenium beautifulsoup4 html2text requests

# Download geckodriver
wget https://github.com/mozilla/geckodriver/releases/download/v0.33.0/geckodriver-v0.33.0-linux64.tar.gz
tar -xvzf geckodriver-v0.33.0-linux64.tar.gz
sudo mv geckodriver /usr/local/bin/
sudo chmod +x /usr/local/bin/geckodriver

# Run the Firefox crawler
python tcia-firefox-crawler.py
