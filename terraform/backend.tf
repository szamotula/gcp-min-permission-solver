terraform {
  backend "gcs" {
    bucket  = "min-permission-solver-terraform-state"
    prefix  = "solver"
  }
}