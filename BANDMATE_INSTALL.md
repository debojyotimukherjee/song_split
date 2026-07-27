# Wannabe Stem Bandmate Install Guide

This is the easiest way for someone in the band to run Wannabe Stem without knowing Python, Git, or terminal commands.

## What They Need First

Install Docker Desktop:

- Mac: https://www.docker.com/products/docker-desktop/
- Windows: https://www.docker.com/products/docker-desktop/

Open Docker Desktop once after installing it. Wait until it says Docker is running.

## Mac

1. Download the Wannabe Stem zip from Google Drive.
2. Unzip it.
3. Open the folder.
4. Double-click **Start Wannabe Stem.command**.
5. If macOS blocks it, right-click the file, choose **Open**, then click **Open** again.
6. The browser should open to http://localhost:8000.

When finished, double-click **Stop Wannabe Stem.command**.

## Windows

1. Download the Wannabe Stem zip from Google Drive.
2. Unzip it.
3. Open the folder.
4. Double-click **Start Wannabe Stem Windows.cmd**.
5. If Windows shows a security warning, click **More info**, then **Run anyway**.
6. The browser should open to http://localhost:8000.

When finished, double-click **Stop Wannabe Stem Windows.cmd**.

## First Run

The first split can take a while because Wannabe Stem downloads the local music separation model. After that, the model is cached on that laptop.

## Where Songs Are Stored

Songs and separated tracks stay inside the `data/` folder in the Wannabe Stem folder. Nothing is uploaded by the app.

## If Something Goes Wrong

- Make sure Docker Desktop is open and running.
- Make sure the folder was unzipped before launching.
- Try the stop script, then start again.
- If port 8000 is already being used by another app, ask Debo for help changing the port.
