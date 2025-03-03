# 🖥️ CPU Monitor Auto-Shutdown Script

![EC2 Meme](assets/ec2.png)

Ever forgotten an **EC2 instance running overnight** and received a **massive AWS bill**? 😨
This script **automatically shuts down idle instances**, saving you from unexpected cloud costs!

The script monitors CPU usage and automatically shuts down the system if usage remains below a specified threshold for a given period. Users can **postpone shutdown manually** or cancel it via an interactive prompt.

---

## 🚀 Features

- ✅ **Monitors CPU usage** and shuts down if below threshold for a set time.
- ✅ **Configurable thresholds and time periods** via environment variables.
- ✅ **Notifies all users before shutdown** with an interactive prompt.
- ✅ **Users can postpone shutdown** manually or interactively.
- ✅ **Prevents postponed shutdown from persisting after a system reboot.**

---

## 📦 Installation Steps

### **1️⃣ Install Required Packages**

Run the following command to install required dependencies:

```sh
sudo apt update && sudo apt install -y python3-pip python3-psutil python3-venv

pip3 install -r requirements.txt
```

### **2️⃣ Clone the Repository**

```sh
git clone <repo-url> && cd <repo-name>
```

### **3️⃣ Deploy the Script**

Copy the script to `/usr/local/bin/`:

```sh
sudo cp monitor.py /usr/local/bin/monitor.py
sudo chmod +x /usr/local/bin/monitor.py
```

### **4️⃣ Deploy the Postpone Shutdown Command**

```sh
sudo cp postpone_shutdown /usr/local/bin/postpone_shutdown
sudo chmod +x /usr/local/bin/postpone_shutdown
```

---

## 🔧 Systemd Service Configuration

### **1️⃣ Create a Systemd Service without Virtualenv**

Create a new systemd service file:

```sh
sudo tee /etc/systemd/system/monitor.service > /dev/null <<EOF
[Unit]
Description=CPU Monitor Shutdown Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 /usr/local/bin/monitor.py
Restart=always
RestartSec=5
StandardOutput=journal+console
StandardError=journal+console
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF
```

### **1️⃣ Run the Service in a Virtual Environment**

Create and Activate a Virtual Environment

```sh
python3 -m venv /opt/cpu_monitor_venv
source /opt/cpu_monitor_venv/bin/activate
```

Install Dependencies Inside Virtualenv

```sh
pip3 install -r requirements.txt
```

Create a new systemd service file:

```sh
sudo tee /etc/systemd/system/monitor.service > /dev/null <<EOF
[Unit]
Description=CPU Monitor Shutdown Service
After=network.target

[Service]
ExecStart=/opt/cpu_monitor_venv/bin/python /usr/local/bin/monitor.py
Restart=always
RestartSec=5
StandardOutput=journal+console
StandardError=journal+console
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF
```

### **2️⃣ Reload Systemd and Enable Service**

```sh
sudo systemctl daemon-reload
sudo systemctl enable monitor.service
sudo systemctl start monitor.service
```

### **3️⃣ Check Service Status**

```sh
sudo systemctl status monitor.service
```

---

## ⚙️ Configuration

You can modify the following **environment variables** before running the script:

| Variable         | Default | Description                                                              |
| ---------------- | ------- | ------------------------------------------------------------------------ |
| `CPU_THRESHOLD`  | `10`    | CPU usage percentage below which the system will shut down.              |
| `CHECK_INTERVAL` | `60`    | Time interval (in seconds) between CPU usage checks.                     |
| `TIME_PERIOD`    | `300`   | Total time (in seconds) CPU must be below the threshold before shutdown. |
| `NOTIFY_PERIOD`  | `60`    | Time (in seconds) before shutdown notification appears.                  |

Example:

```sh
export CPU_THRESHOLD=5
export CHECK_INTERVAL=30
export TIME_PERIOD=600
export NOTIFY_PERIOD=120
```

---

## 🛡️ How to Postpone Shutdown

### **1️⃣ Manually Postpone Shutdown**

You can **postpone shutdown** by running:

```sh
postpone_shutdown <duration>
```

Examples:

```sh
postpone_shutdown 30m  # Postpone for 30 minutes
postpone_shutdown 2h   # Postpone for 2 hours
```

### **2️⃣ Interactive Prompt**

When the system is about to shut down, users will see:

```
🚠 WARNING: System will shut down in 60 seconds due to low CPU utilization!
🚀 Press any key to cancel shutdown or run 'postpone_shutdown <duration>' to delay shutdown.
```

Simply **press any key** to cancel the shutdown.

---

## 📄 Logging & Debugging

Logs can be found in:

```sh
sudo journalctl -u monitor.service -f
```

To check the **postpone status**:

```sh
cat /tmp/monitor_postpone_until
```

---

## 💌 Uninstallation

To remove the script and service:

```sh
sudo systemctl stop monitor.service
sudo systemctl disable monitor.service
sudo rm -f /usr/local/bin/monitor.py /usr/local/bin/postpone_shutdown
sudo rm -f /etc/systemd/system/monitor.service
sudo systemctl daemon-reload
```

---

## 📈 Future Improvements

- [ ] **Implement network monitoring to detect system activity.**
- [ ] **Monitor active SSH sessions to prevent shutdown if users are connected.**

---

## 🛠️ Deploy Using Ansible

All steps in this guide can be automated using **Ansible**.

Run the following command to deploy the script, service, and configurations automatically:

```sh
ansible-playbook -i inventory.ini deploy.yml
```

### 🛠️ Testing With Vagrant
A **Vagrantfile** is included to deploy an Ubuntu VM for testing the script.

To start the VM:

```sh
vagrant up
```

To SSH into the VM:

```sh
vagrant ssh
```

You can then run the Ansible playbook inside the VM for testing the script in an isolated environment.
