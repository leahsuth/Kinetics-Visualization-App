#!/bin/bash

docker run --rm -it -p 8501:8501 -v $(pwd):/app merck-kinetics
