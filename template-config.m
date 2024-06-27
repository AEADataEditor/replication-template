%%% This template file should be copied to the root of the Matlab 
%%% codes of the author, and renamed to "config.m"
%%%


%%% This sets the directory structure type
%%% /* Structure of the code, two scenarios:
%%%    - Code looks like this (simplified, Scenario A)
%%%          directory/
%%%               code/
%%%                  main.m
%%%                  01_dosomething.m
%%%               data/
%%%                  data.dta
%%%                  otherdata.dta
%%%    - Code looks like this (simplified, Scenario B)
%%%          directory/
%%%                main.m
%%%                scripts/
%%%                    01_dosomething.m
%%%                 data/
%%%                    data.dta
%%%                    otherdata.dta
%%%     For the variable "scenario" below, choose "A" or "B". It defaults to "B", since this seems to be more common for Matlab jobs
%%% 
%%%     NOTE: you should always put "config.m" in the same directory as "main.m"
%%% */

scenario = "B"

%%% this dynamically captures the rootdir

[mydir, thisFileName, ~ ] = fileparts(mfilename('fullpath'))

if ~exist('configdone','var')
% do initial config
    if scenario == "A"
        cd ..
        rootdir = pwd
        cd(mydir)
    else
        rootdir = mydir
    end
    configdone = 'TRUE'
end

%%% This captures the version of Matlab and its installed toolboxes.

ver

%%% Any mention elsewhere of hard-coded paths should now be replaced by fullfile(rootdir,'name of file')

% datadir = "../../empirics"
% becomes
% datadir = fullfile(rootdir,"data")

% Special case:
% results = "../results"
% results = "/results" %% if running on Codeocean

%%% Dynare settings
%
% The following are possible Dynare settings. Uncomment the one you need.

% dynarepath = "/Applications/Dynare/4.6.1/matlab"
% dynarepath = "S:\LDILab\dynare\dynare-4.5.7\matlab"
%dynarepath = "L:\common\dynare-4.5.7\matlab"

% 
% Then uncomment the following line:
%
%addpath(genpath(dynarepath))

% 
% display the search path
% 
path
