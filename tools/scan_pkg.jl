#!/usr/bin/env julia

using Pkg
Pkg.add(["CSV", "DataFrames"])
using CSV
using DataFrames

function find_project_packages(project_path)
    packages = Set{String}()
    for (root, dirs, files) in walkdir(project_path)
        for file in files
            if endswith(file, ".jl")
                full_path = joinpath(root, file)
                content = read(full_path, String)
                # Capture 'using' and 'import' statements
                matches = collect(eachmatch(r"(using|import)\s+(\w+)", content))
                for m in matches
                    push!(packages, m.captures[2])
                end
            end
        end
    end
    return packages
end

function main()
    # Check if a directory argument is provided
    if length(ARGS) != 2
        println("Usage: julia dependency_scanner.jl /path/to/project output.csv")
        exit(1)
    end

    project_path = ARGS[1]
    output_path = ARGS[2]

    # Find packages
    packages = find_project_packages(project_path)

    # Convert to DataFrame
    df = DataFrame(Package = collect(packages))

    # Write to CSV
    CSV.write(output_path, df)

    println("Dependencies exported to $(output_path)")
end

main()