# ADWS Folder

This directory contains the AI Developer Workflow System configuration and runtime files for this project.

## Structure

- **config.yaml** - Project-specific ADWS configuration
  - Test command and directories
  - Language settings
  - OpenCode HTTP API configuration
  - Model selection and timeouts

- **logs/** - ADWS execution logs (auto-created)
  - Prompts sent to LLM
  - LLM responses
  - Agent operation logs
  - Error traces

## Configuration

Edit `config.yaml` to customize ADWS for your project:

```yaml
# Change default directories
source_dir: app
test_dir: spec

# Set custom test command
test_command: npm test

# Configure OpenCode models
opencode:
  server_url: "http://localhost:8080"
  timeout: 900
```

See [ADWS Configuration Guide](../../docs/CONFIGURATION.md) for complete options.

## Uninstalling

To remove ADWS from this project, simply delete the `ADWS/` folder:

```bash
rm -rf ADWS/
```

No project configuration files are modified outside this folder.
