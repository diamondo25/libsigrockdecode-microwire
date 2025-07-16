# libsigrockdecode-microwire

This small repository hosts a simplified version of the microwire decoder of libsigrockdecode, which is shipped with PulseView. The changes allow it to work for my usecase.

<img width="1337" height="369" alt="pulseview_2025-07-16_20-02-18" src="https://github.com/user-attachments/assets/39d90aa1-a8bd-4563-ac0b-e1a57143a88a" />


## Changes

- Wait for Start Bit before decoding the bits
- Remove busy/ready logic as that did not work in my usecase.
