Vagrant.configure("2") do |config|
  # Define the base box to use
  config.vm.box = "bento/ubuntu-24.04"

  # Set VM hostname
  config.vm.hostname = ENV['VM_HOSTNAME'] || "ub-srv"

  # Configure network with bridge network
  config.vm.network "public_network", bridge: "enp3s0"

  # Optional: Increase resources for better performance
  config.vm.provider "virtualbox" do |vb|
    vb.memory = ENV['VM_MEMORY'] || "2048"
    vb.cpus = ENV['VM_CPUS'] || 1
  end

  # Print only the eth1 IP after creation
  config.vm.provision "shell", inline: <<-SHELL
    echo "### eth1 IP Address ###"
    ip a
  SHELL
end
