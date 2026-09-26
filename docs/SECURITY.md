# Security Notes

This project is intentionally an educational prototype.

## Implemented in this starter

- Password hashing for the administrator account.
- Server-side face verification.
- Exactly one detected face required for verification/registration.
- Server-side candidate validation.
- Unique `voter_id`.
- Unique `Vote.voter_id` database constraint.
- Session-gated ballot access.
- Audit events for registration, verification and vote casting.
- No raw face image is stored by the application; a face embedding is stored.

## Still required for a serious deployment

1. TLS/HTTPS.
2. CSRF protection on all state-changing forms.
3. Secure/HttpOnly/SameSite session cookie configuration.
4. Rate limiting and abuse monitoring.
5. Strong admin authentication/MFA.
6. Encryption at rest and managed cryptographic keys for biometric data.
7. Formal threat modeling and penetration testing.
8. Liveness/anti-spoofing.
9. Independent auditability of election records.
10. Privacy, retention and deletion policies.
11. Accessibility and assistive-technology testing.
12. High availability, backup and disaster recovery.
13. Independent verification of election results.
14. Compliance with applicable election and biometric-data laws.

A face-recognition match is not, by itself, proof that a camera image comes from a live person. This is why liveness detection is a separate requirement.
