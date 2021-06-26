#!/bin/bash
for arg in $(ls *tex | grep -v pdf_)
do
  echo "\documentclass{article}
	\usepackage[utf8]{inputenc}
	\usepackage{graphicx}
	\usepackage[landscape,margin=0.5in]{geometry}
	\begin{document}
	" > pdf_$arg
	cat $arg >> pdf_$arg
	echo "\end{document}" >> pdf_$arg
	pdflatex pdf_$arg
done
