mod commands;

use clap::{Parser, Subcommand};
use std::process;

#[derive(Parser)]
#[command(
    name = "localdoc",
    about = "Doctown CLI - Create and manage .docpack documentation universes",
    version,
    long_about = "A command-line tool for creating, inspecting, validating, and running AI-powered documentation on .docpack archives."
)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Create a new .docpack from a source (directory, zip, or git repo)
    Ingest {
        /// Path to source directory, zip file, or git URL
        source: String,

        /// Output .docpack directory path
        #[arg(short, long, default_value = "out.docpack")]
        out: String,

        /// Docpack name (defaults to source directory name)
        #[arg(short, long)]
        name: Option<String>,

        /// Description for the docpack
        #[arg(short, long)]
        description: Option<String>,

        /// Primary language of the source code
        #[arg(short, long)]
        language: Option<String>,

        /// Enable all available tools (default: basic subset)
        #[arg(long)]
        all_tools: bool,

        /// Build search index during ingestion
        #[arg(long)]
        build_index: bool,

        /// Build semantic graph during ingestion
        #[arg(long)]
        build_graph: bool,
    },

    /// Run the documenter agent on a .docpack
    Run {
        /// Path to .docpack directory
        docpack: String,

        /// Docker image to use
        #[arg(short, long, default_value = "doctown:latest")]
        image: String,

        /// Follow logs in real-time
        #[arg(short, long)]
        follow: bool,
    },

    /// Inspect a .docpack's structure and metadata
    Inspect {
        /// Path to .docpack directory
        docpack: String,

        /// Show detailed information
        #[arg(short, long)]
        verbose: bool,
    },

    /// Validate a .docpack structure against the spec
    Validate {
        /// Path to .docpack directory
        docpack: String,
    },

    /// Initialize a new empty .docpack structure
    Init {
        /// Path for new .docpack directory
        path: String,

        /// Docpack name
        #[arg(short, long)]
        name: Option<String>,

        /// Create a minimal example tasks.json
        #[arg(long)]
        with_tasks: bool,
    },
}

fn main() {
    let cli = Cli::parse();

    let result = match &cli.command {
        Commands::Ingest {
            source,
            out,
            name,
            description,
            language,
            all_tools,
            build_index,
            build_graph,
        } => commands::ingest::run(
            source,
            out,
            name.as_deref(),
            description.as_deref(),
            language.as_deref(),
            *all_tools,
            *build_index,
            *build_graph,
        ),
        Commands::Run {
            docpack,
            image,
            follow,
        } => commands::run::run(docpack, image, *follow),
        Commands::Inspect { docpack, verbose } => commands::inspect::run(docpack, *verbose),
        Commands::Validate { docpack } => commands::validate::run(docpack),
        Commands::Init {
            path,
            name,
            with_tasks,
        } => commands::init::run(path, name.as_deref(), *with_tasks),
    };

    if let Err(e) = result {
        eprintln!("Error: {}", e);
        process::exit(1);
    }
}
