
const bookingForm = document.getElementById("bookingForm");
const formMessage = document.getElementById("formMessage");

const businessWhatsAppNumber = "919542460423";

bookingForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const customerName = document.getElementById("customerName").value.trim();
    const phone = document.getElementById("phone").value.trim();
    const carBrand = document.getElementById("carBrand").value;
    const carModel = document.getElementById("carModel").value.trim();
    const service = document.getElementById("service").value;
    const date = document.getElementById("date").value;
    const details = document.getElementById("details").value.trim();

    if (!customerName || !phone || !carBrand || !carModel || !service) {
        formMessage.textContent = "Please fill all required fields.";
        return;
    }

    const booking = {
        customer_name: customerName,
        phone: phone,
        car_brand: carBrand,
        car_model: carModel,
        service: service,
        date: date,
        details: details
    };

    const message = `
NEW SERVICE BOOKING
BOOST BOYZ AUTOMOTIVE

Customer Name: ${customerName}
Customer Phone: ${phone}
Car Brand: ${carBrand}
Car Model: ${carModel}
Required Service: ${service}
Preferred Date: ${date || "Not specified"}
Additional Details: ${details || "None"}

YOUR DRIVE. OUR PASSION.
`;

    const whatsappURL =
        "https://wa.me/" + businessWhatsAppNumber +
        "?text=" + encodeURIComponent(message);

    const submitButton = bookingForm.querySelector(
        'button[type="submit"], input[type="submit"]'
    );

    if (submitButton) submitButton.disabled = true;
    formMessage.textContent = "Saving your booking...";

    try {
        const response = await fetch("/api/bookings", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(booking)
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "Could not save booking.");
        }

        formMessage.textContent =
            "Booking saved successfully! Booking ID: " +
            result.booking_id + ". Opening WhatsApp...";

        window.location.href = whatsappURL;

    } catch (error) {
        formMessage.textContent =
            "Booking save nahi hui. Please check that Flask is running and try again.";
        console.error(error);
    } finally {
        if (submitButton) submitButton.disabled = false;
    }
});
