#include <linux/module.h>
#include <linux/init.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/uaccess.h>
#include <linux/gpio/consumer.h>
#include <linux/delay.h>

#define DEVICE_NAME "birdclassifier"
#define CLASS_NAME  "bird"

// Change this to the GPIO pin you have wired (e.g., 17 for Pin 11)
#define LED_GPIO_PIN 17 

static int major;
static struct class* bird_class  = NULL;
static struct device* bird_device = NULL;
struct gpio_desc *led_gpio = NULL;

static ssize_t bird_write(struct file *filp, const char __user *buf, size_t count, loff_t *f_pos)
{
    char kbuf[64];
    size_t len = min(count, sizeof(kbuf) - 1);

    if (copy_from_user(kbuf, buf, len)) {
        return -EFAULT;
    }
    kbuf[len] = '\0';

    // Parse the string: looking for the ':' separator
    if (strstr(kbuf, ":")) {
        printk(KERN_INFO "AviAlert: Valid classification received: %s", kbuf);
        
        // Assert GPIO (Turn LED ON)
        if (led_gpio) {
            gpiod_set_value(led_gpio, 1);
            mdelay(500); // Visible toggle
            gpiod_set_value(led_gpio, 0);
        }
    } else {
        printk(KERN_WARNING "AviAlert: Invalid format received. Use 'name:score'\n");
    }

    return count;
}

static struct file_operations fops = {
    .owner = THIS_MODULE,
    .write = bird_write,
};

static int __init bird_init(void) {
    major = register_chrdev(0, DEVICE_NAME, &fops);
    if (major < 0) return major;

    bird_class = class_create(THIS_MODULE, CLASS_NAME);
    bird_device = device_create(bird_class, NULL, MKDEV(major, 0), NULL, DEVICE_NAME);

    // Request GPIO pin - using 'gpiod_get_from_dt' is standard, 
    // but for manual pin control, we use the descriptor-based approach
    // We'll use a hack for manual assignment in this lab context:
    led_gpio = gpio_to_desc(LED_GPIO_PIN);
    if (led_gpio) {
        gpiod_direction_output(led_gpio, 0);
    }

    printk(KERN_INFO "AviAlert: Driver loaded, LED on GPIO %d\n", LED_GPIO_PIN);
    return 0;
}

static void __exit bird_exit(void) {
    gpiod_set_value(led_gpio, 0);
    device_destroy(bird_class, MKDEV(major, 0));
    class_unregister(bird_class);
    class_destroy(bird_class);
    unregister_chrdev(major, DEVICE_NAME);
    printk(KERN_INFO "AviAlert: Driver unloaded\n");
}

module_init(bird_init);
module_exit(bird_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Atharv More");
MODULE_DESCRIPTION("AviAlert Bird Classifier GPIO Trigger");
