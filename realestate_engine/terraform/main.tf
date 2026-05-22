terraform {
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
    }
  }
}

# Local files for MVP deployment
resource "local_file" "requirements" {
  content  = file("${path.module}/../requirements.txt")
  filename = "${path.module}/../requirements.txt"
}

resource "local_file" "env_example" {
  content  = file("${path.module}/../.env.example")
  filename = "${path.module}/../.env.example"
}
