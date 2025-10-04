# About timona
A command line tool to automate Helm deployments.

In Romanian language "timona" `/tiˈmona/` is the ship's wheel.

# What can it do ?
Starting from an yaml configuration file placed in the root of a helm chart you can:
* describe helm releases using a templating language and create an environment for each release which will be used to generate, with the same templating engine, the helm value file,
* test your deployment independent from the kubernetes cluster (_helm template_) or by connecting to the cluster (_dry-run helm install_),
* deploy, delete, get status of releases,
* view differences between config and deployed versions (_helm diff_).

# Help
For usage see https://github.com/mihaiush/timona/wiki .
