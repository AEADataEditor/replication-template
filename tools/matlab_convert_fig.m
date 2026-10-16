% matlab_convert_fig.m - Convert MATLAB .fig files to PNG format
%
% DESCRIPTION:
%   This script automatically converts all MATLAB figure files (.fig) in the
%   current working directory to PNG format. It preserves the original filename
%   and creates corresponding .png files.
%
% USAGE:
%   Run this script from within MATLAB in the directory containing .fig files:
%   >> matlab_convert_fig
%   
%   Or from command line:
%   matlab -batch "cd('path/to/fig/files'); matlab_convert_fig"
%
% INPUT:
%   - All .fig files in the current working directory
%
% OUTPUT:
%   - PNG files with the same base filename as the original .fig files
%   - Example: 'figure1.fig' -> 'figure1.png'
%
% BEHAVIOR:
%   - Processes all .fig files in the current directory
%   - Opens each figure file and saves it as PNG
%   - Handles multiple figures within a single .fig file
%   - Automatically exits MATLAB when complete
%
% DEPENDENCIES:
%   - MATLAB with figure handling capabilities
%   - Read access to .fig files in current directory
%   - Write access to current directory for PNG output
%
% NOTE:
%   This script will exit MATLAB upon completion. Use with caution in
%   interactive sessions.

% Get current working directory and set output format
myDir = pwd
convertto = "png"

% Get all .fig files in the current directory
myFiles = dir(fullfile(myDir,'*.fig')); % Gets all fig files in struct
% Process each .fig file found
for k = 1:length(myFiles)
    % Extract filename components
    baseFileName = myFiles(k).name;
    [p,baseName,extension] = fileparts(baseFileName);
    
    % Display progress
    fprintf(1, 'Now reading %s\n', baseFileName);
    
    % Open the figure file (may contain multiple figures)
    figs = openfig(baseFileName);
    
    % Save each figure in the file as PNG
    for K = 1 : length(figs)
        % Construct output filename with PNG extension
        newfilename = fullfile(baseName + "." + convertto)
        
        % Save the figure as PNG
        saveas(figs(K), newfilename);
    end
end

% Exit MATLAB when conversion is complete
exit


