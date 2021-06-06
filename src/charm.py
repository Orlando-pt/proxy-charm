#!/usr/bin/env python3
# Copyright 2020 David Garcia
# See LICENSE file for licensing details.
#
# Further developed by Orlando Macedo 2021
# email: orlando.macedo15@ua.pt

from ops.main import main

from charms.osm.sshproxy import SSHProxyCharm
from ops.model import (
    ActiveStatus,
    MaintenanceStatus,
    BlockedStatus,
    WaitingStatus,
    ModelError,
)

class SshproxyCharm(SSHProxyCharm):
    def __init__(self, *args):
        super().__init__(*args)

        # An example of setting charm state
        # that's persistent across events
        self.state.set_default(is_started=False)

        if not self.state.is_started:
            self.state.is_started = True

        # Register all of the events we want to observe
        # Charm events
        self.framework.observe(self.on.config_changed, self.on_config_changed)
        self.framework.observe(self.on.install, self.on_install)
        self.framework.observe(self.on.start, self.on_start)
        self.framework.observe(self.on.upgrade_charm, self.on_upgrade_charm)
        # Charm actions (primitives)
        self.framework.observe(self.on.touch_action, self.on_touch_action)
        # OSM actions (primitives)
        self.framework.observe(self.on.start_action, self.on_start_action)
        self.framework.observe(self.on.stop_action, self.on_stop_action)
        self.framework.observe(self.on.restart_action, self.on_restart_action)
        self.framework.observe(self.on.reboot_action, self.on_reboot_action)
        self.framework.observe(self.on.upgrade_action, self.on_upgrade_action)

        # Personalized actions
        self.framework.observe(self.on.clone_github_repository_action,
                                        self.on_clone_github_repository_action)
        self.framework.observe(
            self.on.update_repository_action,
            self.on_update_repository_action
        )
        self.framework.observe(
            self.on.delete_repository_action,
            self.on_delete_repository_action
        )

        self.framework.observe(self.on.run_app_action, self.on_run_app_action)
        self.framework.observe(self.on.stop_app_action, self.on_stop_app_action)
        self.framework.observe(self.on.start_app_action, self.on_start_app_action)
        self.framework.observe(self.on.remove_app_action, self.on_remove_app_action)

        # specific vars
        self.github_dir = "~/github-code/"

    def on_config_changed(self, event):
        """Handle changes in configuration"""
        super().on_config_changed(event)

    def on_install(self, event):
        super().on_install(event)

    def on_start(self, event):
        """Called when the charm is being installed"""
        super().on_start(event)

    def on_upgrade_charm(self, event):
        """Upgrade the charm."""
        self.unit.status = MaintenanceStatus("Upgrading charm")
        # Do upgrade related stuff
        self.unit.status = ActiveStatus("Active")

    def on_touch_action(self, event):
        """Touch a file."""

        if self.unit.is_leader():
            filename = event.params["filename"]
            proxy = self.get_ssh_proxy()
            stdout, stderr = proxy.run("touch {}".format(filename))
            proxy.scp("/etc/lsb-release", "/home/ubuntu/scp_file")
            event.set_results({"output": stdout})
        else:
            event.fail("Unit is not leader")
            return

    ###############
    # OSM methods #
    ###############
    def on_start_action(self, event):
        """Start the VNF service on the VM."""
        if self.unit.is_leader():
            self.unit.status = MaintenanceStatus("Installing docker")
            proxy = self.get_ssh_proxy()

            # install docker
            proxy.run("sudo apt-get update")
            proxy.run("sudo apt-get -y install apt-transport-https" + 
                                        " ca-certificates" + 
                                        " curl" +
                                        " gnupg" +
                                        " lsb-release")
            proxy.run("curl -fsSL https://download.docker.com/linux/ubuntu/gpg | " +
                        "sudo gpg --yes --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg")
            proxy.run("echo \"deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] " +
                        "https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable\"" + 
                        " | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null")
            proxy.run("sudo apt-get update")
            proxy.run("sudo apt-get -y install docker-ce docker-ce-cli containerd.io")

            # install docker-compose
            self.unit.status = MaintenanceStatus("Installing docker-compose")
            
            #proxy.run("sudo groupadd docker")
            proxy.run("sudo usermod -aG docker $USER")
            proxy.run("newgrp docker")
            proxy.run("sudo chown root:docker /var/run/docker.sock")
            proxy.run("sudo chown -R root:docker /var/run/docker")

            proxy.run("sudo curl -L \"https://github.com/docker/compose/releases/latest/download" + 
                "/docker-compose-$(uname -s)-$(uname -m)\" " + 
                "-o /usr/local/bin/docker-compose && sudo chmod +x /usr/local/bin/docker-compose")

            # add directory where the github repository code will be placed
            proxy.run("mkdir {}".format(self.github_dir))
            
            self.unit.status = ActiveStatus("All required packages installed successfully")
        else:
            event.fail("Unit is not leader")
            return

    def on_stop_action(self, event):
        """Stop the VNF service on the VM."""
        if self.unit.is_leader():
            self.unit.status = MaintenanceStatus("Removing docker")
            proxy = self.get_ssh_proxy()

            # stop all running containers
            proxy.run("docker stop $(docker ps -q)")

            # remove containers
            proxy.run("docker rm $(docker ps -a -q)")

            # remove all docker images
            proxy.run("docker image rm $(docker images -q)")
            
            # removing docker installation
            proxy.run("sudo apt-get -y purge docker-ce docker-ce-cli containerd.io")
            proxy.run("sudo apt-get -y autoremove")
            proxy.run("sudo rm -rf /var/lib/docker")
            proxy.run("sudo rm -rf /var/lib/containerd")
            proxy.run("sudo rm /var/run/docker.sock")
            proxy.run("sudo rm -rf /var/run/docker/")

            self.unit.status = MaintenanceStatus("Removing docker-compose")
            proxy.run("newgrp ubuntu")
            proxy.run("sudo deluser $USER docker")
            proxy.run("sudo groupdel docker")
            proxy.run("sudo rm /usr/local/bin/docker-compose")

            # remove github code
            proxy.run("rm -rf {}".format(self.github_dir))

            self.unit.status = ActiveStatus("All the installed packages were removed")
        else:
            event.fail("Unit is not leader")
            return

    def on_restart_action(self, event):
        """Restart the VNF service on the VM."""
        pass

    def on_reboot_action(self, event):
        """Reboot the VM."""
        if self.unit.is_leader():
            proxy = self.get_ssh_proxy()
            stdout, stderr = proxy.run("sudo reboot")
            if len(stderr):
                event.fail(stderr)
        else:
            event.fail("Unit is not leader")
            return

    def on_upgrade_action(self, event):
        """Upgrade the VNF service on the VM."""
        pass

    ########################
    # Personalized methods #
    ########################
    def on_clone_github_repository_action(self, event):
        """ Clone github repository to the VNF service on the VM """
        if self.unit.is_leader():
            proxy = self.get_ssh_proxy()
            app_name = event.params["app-name"]

            self.unit.status = MaintenanceStatus("Cloning repository")

            proxy.run("git clone {} {}{}".format(event.params["repository-url"],
                                    self.github_dir, app_name))

            self.unit.status = ActiveStatus("Repository Cloned")
        else:
            event.fail("Unit is not leader")
            return

    def on_update_repository_action(self, event):
        """ Update repository on the VM associated with the VNF service """
        if self.unit.is_leader():
            proxy = self.get_ssh_proxy()

            self.unit.status = MaintenanceStatus("Updating repository")


            proxy.run("cd {}{} && git pull".format(self.github_dir, event.params["app-name"]))

            self.unit.status = ActiveStatus("Repository updated")
        else:
            event.fail("Unit is not leader")
            return        
    
    def on_delete_repository_action(self, event):
        """ Delete repository on the VM associated with the VNF service """
        if self.unit.is_leader():
            proxy = self.get_ssh_proxy()
            app_name = event.params["app-name"]

            self.unit.status = MaintenanceStatus("Deleting repository")

            proxy.run("rm -rf {}{}/".format(self.github_dir, app_name))

            self.unit.status = ActiveStatus("Repository deleted")
        else:
            event.fail("Unit is not leader")
            return 

    def on_run_app_action(self, event):
        """ Build and run application on the VM associated with the VNF service """
        if self.unit.is_leader():
            app_name = event.params["app-name"]
            
            proxy = self.get_ssh_proxy()
            self.unit.status = MaintenanceStatus("Building and running application {}".format(app_name))

            proxy.run("docker-compose -f {}{}/docker-compose.yml up -d".format(self.github_dir, app_name))

            self.unit.status = ActiveStatus("{} running successfully".format(app_name))
        else:
            event.fail("Unit is not leader")
            return

    def on_stop_app_action(self, event):
        """ Stop application on the VM associated with the VNF service """
        if self.unit.is_leader():
            app_name = event.params["app-name"]
            
            proxy = self.get_ssh_proxy()
            self.unit.status = MaintenanceStatus("Stoping application {}".format(app_name))

            proxy.run("docker-compose -f {}{}/docker-compose.yml stop".format(self.github_dir, app_name))

            self.unit.status = ActiveStatus("{} stopped successfully".format(app_name))
        else:
            event.fail("Unit is not leader")
            return

    def on_start_app_action(self, event):
        """ Start application on the VM associated with the VNF service """
        if self.unit.is_leader():
            app_name = event.params["app-name"]
            
            proxy = self.get_ssh_proxy()
            self.unit.status = MaintenanceStatus("Starting application {}".format(app_name))

            proxy.run("docker-compose -f {}{}/docker-compose.yml start".format(self.github_dir, app_name))

            self.unit.status = ActiveStatus("{} started successfully".format(app_name))
        else:
            event.fail("Unit is not leader")
            return

    def on_remove_app_action(self, event):
        """ Remove application on the VM associated with the VNF service """
        if self.unit.is_leader():
            app_name = event.params["app-name"]
            
            proxy = self.get_ssh_proxy()
            self.unit.status = MaintenanceStatus("Removing application {}".format(app_name))

            proxy.run("docker-compose -f {}{}/docker-compose.yml down".format(self.github_dir, app_name))

            # remove docker images related to the app
            proxy.run("docker image rm $(docker images -f=reference=\"{}*:*\" -q)".format(app_name))

            self.unit.status = ActiveStatus("{} removed successfully".format(app_name))
        else:
            event.fail("Unit is not leader")
            return


if __name__ == "__main__":
    main(SshproxyCharm)
