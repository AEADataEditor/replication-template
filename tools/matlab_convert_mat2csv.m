% convert Mat files to csv

myDir = pwd
convertto = "csv"

myFiles = dir(fullfile(myDir,'*.mat')); %gets all mat files in struct
for k = 1:length(myFiles)
  baseFileName = myFiles(k).name;
  [p,baseName,extension]=fileparts(baseFileName);
  fprintf(1, 'Now reading %s\n', baseFileName);
  mat = load(baseFileName);
  f   = fieldnames(mat);  % this is the table name, probably
  for k = 1: size(f,1)
      newfilename =  fullfile(f{k} + "." + convertto)
      writematrix(mat.(f{k}),newfilename)
  end
end
exit

