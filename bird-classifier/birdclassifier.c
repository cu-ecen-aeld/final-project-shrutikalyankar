#include <linux/module.h>
#include <linux/init.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/uaccess.h>
#include <linux/gpio.h>         // For legacy gpio_request
#include <linux/gpio/consumer.h> // For gpiod_set_value
#include <linux/delay.h>
#include <linux/wait.h>
#include <linux/sched.h>
#include <linux/ioctl.h>

#define DEVICE_NAME "birdclassifier"
#define CLASS_NAME  "bird"
#define LED_GPIO_PIN 17 

/* IOCTL Definitions */
#define BIRD_IOC_MAGIC 'b'
#define BIRD_GET_STATE _IOR(BIRD_IOC_MAGIC, 1, int)

static int major;
static struct class* bird_class  = NULL;
static struct device* bird_device = NULL;
struct gpio_desc *led_gpio = NULL;

/* Wait Queue and Data Buffering */
static DECLARE_WAIT_QUEUE_HEAD(read_queue);
static char result_buffer[64];
static bool data_available = false;
static int birds_detected_count = 0;

/**
 * bird_read - Blocks until a new classification is written
 */
static ssize_t bird_read(struct file *filp, char __user *buf, size_t count, loff_t *f_pos)
{
    size_t len;

    // Block until data_available is true
    if (wait_event_interruptible(read_queue, data_available)) {
        return -ERESTARTSYS;
    }

    len = strlen(result_buffer);
    if (count < len) len = count;

    if (copy_to_user(buf, result_buffer, len)) {
        return -EFAULT;
    }

    data_available = false; 
    return len;
}

/**
 * bird_write - Receives classification, toggles LED, and wakes up readers
 */
static ssize_t bird_write(struct file *filp, const char __user *buf, size_t count, loff_t *f_pos)
{
    char kbuf[64];
    size_t len = min(count, sizeof(kbuf) - 1);

    if (copy_from_user(kbuf, buf, len)) {
        return -EFAULT;
    }
    kbuf[len] = '\0';

    if (strstr(kbuf, ":")) {
        strncpy(result_buffer, kbuf, sizeof(result_buffer));
        data_available = true;
        birds_detected_count++;

        printk(KERN_INFO "AviAlert: Bird detected! Pulse LED and wake readers.\n");
        
        // Assert GPIO (Toggle LED)
        if (led_gpio) {
            gpiod_set_value(led_gpio, 1);
            mdelay(500); 
            gpiod_set_value(led_gpio, 0);
        }

        wake_up_interruptible(&read_queue);
    }

    return count;
}

/**
 * bird_ioctl - Returns the total count of birds detected
 */
static long bird_ioctl(struct file *filp, unsigned int cmd, unsigned long arg)
{
    switch(cmd) {
        case BIRD_GET_STATE:
            if (copy_to_user((int __user *)arg, &birds_detected_count, sizeof(birds_detected_count)))
                return -EFAULT;
            break;
        default:
            return -ENOTTY;
    }
    return 0;
}

static struct file_operations fops = {
    .owner = THIS_MODULE,
    .read = bird_read,
    .write = bird_write,
    .unlocked_ioctl = bird_ioctl,
};

static int __init bird_init(void) {
    int ret;

    // 1. Character Device Setup
    major = register_chrdev(0, DEVICE_NAME, &fops);
    if (major < 0) return major;

    bird_class = class_create(THIS_MODULE, CLASS_NAME);
    if (IS_ERR(bird_class)) {
        unregister_chrdev(major, DEVICE_NAME);
        return PTR_ERR(bird_class);
    }

    bird_device = device_create(bird_class, NULL, MKDEV(major, 0), NULL, DEVICE_NAME);
    if (IS_ERR(bird_device)) {
        class_destroy(bird_class);
        unregister_chrdev(major, DEVICE_NAME);
        return PTR_ERR(bird_device);
    }

    // 2. EXPLICIT GPIO REQUEST (Fixes the "unclaimed" issue)
    ret = gpio_request(LED_GPIO_PIN, "birdclassifier");
    if (ret) {
        printk(KERN_ERR "AviAlert: Failed to request GPIO %d\n", LED_GPIO_PIN);
        device_destroy(bird_class, MKDEV(major, 0));
        class_destroy(bird_class);
        unregister_chrdev(major, DEVICE_NAME);
        return ret;
    }

    // 3. Set direction and map to descriptor
    gpio_direction_output(LED_GPIO_PIN, 0);
    led_gpio = gpio_to_desc(LED_GPIO_PIN);

    printk(KERN_INFO "AviAlert: Advanced Driver loaded. GPIO 17 claimed.\n");
    return 0;
}

static void __exit bird_exit(void) {
    if (led_gpio) {
        gpiod_set_value(led_gpio, 0);
    }
    
    // Release the GPIO pin
    gpio_free(LED_GPIO_PIN);

    device_destroy(bird_class, MKDEV(major, 0));
    class_unregister(bird_class);
    class_destroy(bird_class);
    unregister_chrdev(major, DEVICE_NAME);
    
    printk(KERN_INFO "AviAlert: Advanced Driver unloaded.\n");
}

module_init(bird_init);
module_exit(bird_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Atharv More");
MODULE_DESCRIPTION("AviAlert Advanced Character Driver with GPIO Control");