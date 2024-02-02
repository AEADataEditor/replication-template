myDir = pwd
convertto = "png"

myFiles = dir(fullfile(myDir,'*.fig')); %gets all fig files in struct
for k = 1:length(myFiles)
  baseFileName = myFiles(k).name;
  [p,baseName,extension]=fileparts(baseFileName);
  fprintf(1, 'Now reading %s\n', baseFileName);
  figs = openfig(baseFileName);
  for K = 1 : length(figs)
      newfilename =  fullfile(baseName + "." + convertto)
      saveas(figs(K), newfilename);
  end
end
exit


