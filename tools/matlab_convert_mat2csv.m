% matlab_convert_mat2csv.m - Convert MATLAB .mat files to CSV format
%
% DESCRIPTION:
%   This script automatically converts all MATLAB data files (.mat) in the
%   current working directory to CSV format. It extracts all variables from
%   each .mat file and saves them as separate CSV files.
%
% USAGE:
%   Run this script from within MATLAB in the directory containing .mat files:
%   >> matlab_convert_mat2csv
%   
%   Or from command line:
%   matlab -batch "cd('path/to/mat/files'); matlab_convert_mat2csv"
%
% INPUT:
%   - All .mat files in the current working directory
%   - .mat files should contain numeric matrices or tables
%
% OUTPUT:
%   - CSV files named after the variable names within each .mat file
%   - Example: If 'data.mat' contains variables 'results' and 'summary',
%     outputs will be 'results.csv' and 'summary.csv'
%
% BEHAVIOR:
%   - Processes all .mat files in the current directory
%   - Loads each .mat file and extracts all variables
%   - Creates separate CSV files for each variable
%   - Uses variable names as CSV filenames
%   - Automatically exits MATLAB when complete
%
% DEPENDENCIES:
%   - MATLAB with file I/O capabilities
%   - Read access to .mat files in current directory
%   - Write access to current directory for CSV output
%   - writematrix function (MATLAB R2019a or later)
%
% LIMITATIONS:
%   - Only works with numeric matrices and tables
%   - Complex data structures may not convert properly
%   - Cell arrays and nested structures are not supported
%
% NOTE:
%   This script will exit MATLAB upon completion. Use with caution in
%   interactive sessions.

% Get current working directory and set output format
myDir = pwd
convertto = "csv"

% Get all .mat files in the current directory
myFiles = dir(fullfile(myDir,'*.mat')); % Gets all mat files in struct
% Process each .mat file found
for k = 1:length(myFiles)
    % Extract filename components
    baseFileName = myFiles(k).name;
    [p,baseName,extension] = fileparts(baseFileName);
    
    % Display progress
    fprintf(1, 'Now reading %s\n', baseFileName);
    
    % Load the .mat file into a structure
    mat = load(baseFileName);
    
    % Get all variable names from the loaded structure
    f = fieldnames(mat);  % Variable names become fieldnames
    
    % Process each variable in the .mat file
    for j = 1: size(f,1)
        % Construct output filename using variable name
        newfilename = fullfile(f{j} + "." + convertto)
        
        % Write the variable data to CSV file
        % Note: writematrix works with numeric matrices and tables
        writematrix(mat.(f{j}), newfilename)
    end
end

% Exit MATLAB when conversion is complete
exit

