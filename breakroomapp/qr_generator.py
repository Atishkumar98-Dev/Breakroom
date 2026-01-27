import qrcode

# 1) The link you shared
url = "https://maps.app.goo.gl/7HAQLEX16WXdSBGE8?g_st=ic"

# 2) Create QR code object
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=10,
    border=4,
)

qr.add_data(url)
qr.make(fit=True)

# 3) Generate image
img = qr.make_image(fill_color="black", back_color="white")

# 4) Save to file
output_file = "maps_qr.png"
img.save(output_file)

print(f"QR code saved to {output_file}")
