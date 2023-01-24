locals {
  permission_lists   = jsondecode(file("${path.module}/permissions.json")).permission_lists
  variables          = jsondecode(file("${path.module}/variables.json"))
  project            = local.variables["project"]
  service_account_id = local.variables["service_account_id"]
}

resource "google_service_account" "this" {
  project    = local.project
  account_id = local.service_account_id
}

resource "google_project_iam_custom_role" "dynamic" {
  count       = length(local.permission_lists)
  project     = local.project
  role_id     = "MinPermissionSolverRole${count.index}"
  title       = "Minimum Permission Solver Role (${count.index})"
  description = "A custom role for solving minimum permissions"
  permissions = local.permission_lists[count.index]
}

resource "google_project_iam_member" "dynamic" {
  count   = length(local.permission_lists)
  project = local.project
  role    = google_project_iam_custom_role.dynamic[count.index].id
  member  = "serviceAccount:${google_service_account.this.email}"
}
