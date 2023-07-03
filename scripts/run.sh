if [[ "$VIRTUAL_ENV" == "" ]]; then
    if [ ! -d "venv" ]; then
        echo "No venv was found. Creating..."
        python3 -m venv venv
    fi

    source venv/bin/activate
fi

python3 run.py
