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
- ✅ **Time-restricted monitoring** - Only monitors during specified hours (configurable).
- ✅ **SSH session detection** - Prevents shutdown when active SSH sessions are detected.
- ✅ **Enhanced logging** with structured log format and rotation.
- ✅ **Improved postpone mechanism** with system uptime tracking.

---

## 📦 Installation Steps

### **1️⃣ Install Required Packages**

Run the following command to install required dependencies:

```sh
sudo apt update && sudo apt install -y python3-pip python3-psutil python3-venv

# Install Python dependencies
pip3 install -r requirements.txt
```

### **2️⃣ Deploy the Script**

Copy the script to `/usr/local/bin/`:

```sh
sudo cp monitor.py /usr/local/bin/monitor.py
sudo chmod +x /usr/local/bin/monitor.py
```

### **3️⃣ Deploy the Postpone Shutdown Command**

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

| Variable                        | Default | Description                                                                      |
| ------------------------------- | ------- | -------------------------------------------------------------------------------- |
| `CPU_THRESHOLD`                 | `10`    | CPU usage percentage below which the system will shut down.                     |
| `CHECK_INTERVAL`                | `60`    | Time interval (in seconds) between CPU usage checks.                            |
| `TIME_PERIOD`                   | `3600`  | Total time (in seconds) CPU must be below the threshold before shutdown.        |
| `NOTIFY_PERIOD`                 | `300`   | Time (in seconds) before shutdown notification appears.                         |
| `ALLOWED_START_HOUR`            | `19`    | Hour (24h format) when monitoring starts (UTC timezone).                       |
| `ALLOWED_END_HOUR`              | `8`     | Hour (24h format) when monitoring ends (UTC timezone).                         |
| `RESTRICTED_HOURS`              | `true`  | Enable/disable time-restricted monitoring (`true` or `false`).                  |
| `DENY_TURN_OFF_WHEN_ACTIVE_SSH` | `true`  | Prevent shutdown when active SSH sessions are detected (`true` or `false`).     |

### **Time-Restricted Monitoring**

By default, the script only monitors between **19:00 and 08:00 UTC**. This prevents accidental shutdowns during typical working hours. You can:

- **Disable time restrictions**: Set `RESTRICTED_HOURS=false`
- **Customize monitoring window**: Adjust `ALLOWED_START_HOUR` and `ALLOWED_END_HOUR`

### **SSH Session Protection**

The script automatically detects active SSH sessions and prevents shutdown to avoid interrupting user work. To disable this feature:

```sh
export DENY_TURN_OFF_WHEN_ACTIVE_SSH=false
```

Example configuration:

```sh
export CPU_THRESHOLD=5
export CHECK_INTERVAL=30
export TIME_PERIOD=600
export NOTIFY_PERIOD=120
export ALLOWED_START_HOUR=20
export ALLOWED_END_HOUR=7
export RESTRICTED_HOURS=true
export DENY_TURN_OFF_WHEN_ACTIVE_SSH=true
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
postpone_shutdown 15s  # Postpone for 15 seconds
```

The postpone mechanism now includes **system uptime tracking** to prevent postponed shutdowns from persisting after system reboots.

### **2️⃣ Interactive Prompt**

When the system is about to shut down, users will see:

```
⚠️ WARNING: System will shut down in 300 seconds due to low CPU utilization!
🚀 Press any key to cancel shutdown or run 'postpone_shutdown <duration>' to delay shutdown.
```

Simply **press any key** to cancel the shutdown and automatically postpone it for **10 minutes**.

---

## 📄 Logging & Debugging

The script uses **structured logging** with automatic log rotation. Logs are written to multiple locations:

### **System Logs**
```sh
# View system service logs
sudo journalctl -u monitor.service -f

# View dedicated log file (with rotation)
sudo tail -f /var/log/cpu_monitor.log
```

### **Log Format**
The script uses a structured log format:
```
2025-09-14 12:30:45 | INFO | 🚀 CPU Monitor Script Started
2025-09-14 12:30:45 | INFO | 📊 CPU Usage: 5.23% (Threshold: 10%)
2025-09-14 12:30:45 | INFO | ✅ 1/60 readings below threshold.
```

### **Check Postpone Status**
```sh
cat /tmp/cpu_monitor_postpone_until
```

### **Debug Configuration**
The script logs all configuration values on startup:
```sh
sudo journalctl -u monitor.service | grep "Loaded Configuration" -A 10
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

## 📈 Recent Improvements & Future Ideas

### ✅ **Recently Implemented**
- ✅ **SSH session monitoring** - System prevents shutdown when active SSH sessions are detected
- ✅ **Time-restricted monitoring** - Configurable monitoring hours to prevent daytime shutdowns
- ✅ **Enhanced logging** - Structured logging with automatic rotation using loguru
- ✅ **Improved postpone mechanism** - System uptime tracking prevents postpone persistence after reboots
- ✅ **Better configuration** - Comprehensive environment variable support with logging

### 🔮 **Future Ideas**
- [ ] **Network activity monitoring** to detect system activity beyond CPU usage
- [ ] **Web dashboard** for remote monitoring and control
- [ ] **Slack/Discord notifications** before shutdown

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
