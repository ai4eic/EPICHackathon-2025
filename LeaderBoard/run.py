import argparse, os
from dotenv import load_dotenv
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Leaderboard")
    parser.add_argument("--env", "-e", type = str, required = True, help = "Environment to run the app")
    args = parser.parse_args()
    if not os.path.exists(args.env):
        print ("Environment file does not exist")
        exit()
    envfile = args.env
    load_dotenv(envfile)
    from leaderboard import app
    from leaderboard import db
    with app.app_context():
        db.create_all()
        print ("Database created")
    app.run(debug=True)