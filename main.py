import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.join(current_dir, ".venv"), "bin"))
sys.path.insert(0, os.path.join(current_dir, "bin"))

def main():
    print("Hello from sqlite-rx-multi!")
    print(sys.path)

if __name__ == "__main__":
    main()
