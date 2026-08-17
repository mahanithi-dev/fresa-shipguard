from pathlib import Path
import runpy

def main():
    # run the training module inside the backend package
    runpy.run_path('backend/app/ml/train_model.py', run_name='__main__')

if __name__ == '__main__':
    main()
