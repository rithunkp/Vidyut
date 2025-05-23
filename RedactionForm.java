import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.io.IOException;
import java.nio.file.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class RedactionForm extends JFrame {

    private JTextField emailField, phoneField, creditCardField, passportField, residentIdField, bankAccountField;
    private JTextArea outputArea;
    private JButton redactButton;

    public RedactionForm() {
        super("Sensitive Data Redaction Form");
        setDefaultCloseOperation(EXIT_ON_CLOSE);
        setSize(600, 600);
        setLocationRelativeTo(null);

        initComponents();
    }

    private void initComponents() {
        JPanel formPanel = new JPanel();
        formPanel.setLayout(new GridBagLayout());
        GridBagConstraints gbc = new GridBagConstraints();

        JLabel emailLabel = new JLabel("Email:");
        JLabel phoneLabel = new JLabel("Phone Number:");
        JLabel creditCardLabel = new JLabel("Credit Card Number:");
        JLabel passportLabel = new JLabel("Passport Number:");
        JLabel residentIdLabel = new JLabel("Resident ID:");
        JLabel bankAccountLabel = new JLabel("Bank Account Number:");

        emailField = new JTextField(30);
        phoneField = new JTextField(30);
        creditCardField = new JTextField(30);
        passportField = new JTextField(30);
        residentIdField = new JTextField(30);
        bankAccountField = new JTextField(30);

        gbc.insets = new Insets(5, 10, 5, 10);
        gbc.anchor = GridBagConstraints.WEST;

        gbc.gridx = 0; gbc.gridy = 0;
        formPanel.add(emailLabel, gbc);
        gbc.gridx = 1;
        formPanel.add(emailField, gbc);

        gbc.gridx = 0; gbc.gridy++;
        formPanel.add(phoneLabel, gbc);
        gbc.gridx = 1;
        formPanel.add(phoneField, gbc);

        gbc.gridx = 0; gbc.gridy++;
        formPanel.add(creditCardLabel, gbc);
        gbc.gridx = 1;
        formPanel.add(creditCardField, gbc);

        gbc.gridx = 0; gbc.gridy++;
        formPanel.add(passportLabel, gbc);
        gbc.gridx = 1;
        formPanel.add(passportField, gbc);

        gbc.gridx = 0; gbc.gridy++;
        formPanel.add(residentIdLabel, gbc);
        gbc.gridx = 1;
        formPanel.add(residentIdField, gbc);

        gbc.gridx = 0; gbc.gridy++;
        formPanel.add(bankAccountLabel, gbc);
        gbc.gridx = 1;
        formPanel.add(bankAccountField, gbc);

        // Redact button
        redactButton = new JButton("Redact Data");

        gbc.gridx = 0; gbc.gridy++;
        gbc.gridwidth = 2;
        gbc.anchor = GridBagConstraints.CENTER;
        formPanel.add(redactButton, gbc);

        // Output area
        outputArea = new JTextArea(10, 50);
        outputArea.setEditable(false);
        outputArea.setFont(new Font("Monospaced", Font.PLAIN, 14));
        JScrollPane scrollPane = new JScrollPane(outputArea);

        // Add everything to frame
        setLayout(new BorderLayout(10, 10));
        add(formPanel, BorderLayout.NORTH);
        add(scrollPane, BorderLayout.CENTER);

        // Button action
        redactButton.addActionListener(e -> redactAndSave());
    }

    private void redactAndSave() {
        // Collect inputs
        String email = emailField.getText().trim();
        String phone = phoneField.getText().trim();
        String creditCard = creditCardField.getText().trim();
        String passport = passportField.getText().trim();
        String residentId = residentIdField.getText().trim();
        String bankAccount = bankAccountField.getText().trim();

        // Build combined input text for demo output
        StringBuilder inputText = new StringBuilder();
        inputText.append("Email: ").append(email).append("\n");
        inputText.append("Phone Number: ").append(phone).append("\n");
        inputText.append("Credit Card Number: ").append(creditCard).append("\n");
        inputText.append("Passport Number: ").append(passport).append("\n");
        inputText.append("Resident ID: ").append(residentId).append("\n");
        inputText.append("Bank Account Number: ").append(bankAccount).append("\n");

        // Redact sensitive data in the combined text
        String redactedText = RedactionLogic.redactSensitiveData(inputText.toString());

        // Show redacted text in output area
        outputArea.setText(redactedText);

        // Save to output.txt
        try {
            Files.write(Paths.get("output.txt"), redactedText.getBytes());
            JOptionPane.showMessageDialog(this, "Redacted data saved to output.txt", "Success",
                    JOptionPane.INFORMATION_MESSAGE);
        } catch (IOException ex) {
            JOptionPane.showMessageDialog(this, "Error saving file: " + ex.getMessage(), "Error",
                    JOptionPane.ERROR_MESSAGE);
        }
    }

    // Inner static class with redaction logic reused from before
    public static class RedactionLogic {
        private static final String EMAIL_REGEX = "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b";
        private static final String PHONE_REGEX = "\\b(\\+\\d{1,3}[- ]?)?\\d{10}\\b";
        private static final String CREDIT_CARD_REGEX = "\\b(?:\\d[ -]*?){13,19}\\b";
        private static final String PASSPORT_REGEX = "\\b([A-Za-z]\\d{7}|[A-Za-z0-9]{9})\\b";
        private static final String RESIDENT_ID_REGEX = "\\b\\d{12}\\b";
        private static final String BANK_ACCOUNT_REGEX = "\\b\\d{8,14}\\b";

        public static String redactSensitiveData(String text) {
            text = maskPhoneNumbers(text);
            text = maskEmails(text);
            text = maskGenericNumber(text, CREDIT_CARD_REGEX);
            text = maskGenericNumber(text, PASSPORT_REGEX);
            text = maskGenericNumber(text, RESIDENT_ID_REGEX);
            text = maskGenericNumber(text, BANK_ACCOUNT_REGEX);
            return text;
        }

        private static String maskPhoneNumbers(String text) {
            Pattern phonePattern = Pattern.compile(PHONE_REGEX);
            Matcher phoneMatcher = phonePattern.matcher(text);
            StringBuffer phoneResult = new StringBuffer();
            while (phoneMatcher.find()) {
                String phone = phoneMatcher.group();
                StringBuilder maskedPhone = new StringBuilder();
                int digitsMasked = 0;
                for (char c : phone.toCharArray()) {
                    if (Character.isDigit(c) && digitsMasked < 5) {
                        maskedPhone.append('*');
                        digitsMasked++;
                    } else {
                        maskedPhone.append(c);
                    }
                }
                phoneMatcher.appendReplacement(phoneResult, maskedPhone.toString());
            }
            phoneMatcher.appendTail(phoneResult);
            return phoneResult.toString();
        }

        private static String maskEmails(String text) {
            Pattern emailPattern = Pattern.compile(EMAIL_REGEX);
            Matcher emailMatcher = emailPattern.matcher(text);
            StringBuffer emailResult = new StringBuffer();
            while (emailMatcher.find()) {
                String email = emailMatcher.group();
                int atIndex = email.indexOf('@');
                if (atIndex > 0) {
                    StringBuilder maskedEmail = new StringBuilder();
                    for (int i = 0; i < atIndex; i++) {
                        maskedEmail.append('*');
                    }
                    maskedEmail.append(email.substring(atIndex));
                    emailMatcher.appendReplacement(emailResult, maskedEmail.toString());
                } else {
                    emailMatcher.appendReplacement(emailResult, email);
                }
            }
            emailMatcher.appendTail(emailResult);
            return emailResult.toString();
        }

        private static String maskGenericNumber(String text, String regex) {
            Pattern pattern = Pattern.compile(regex);
            Matcher matcher = pattern.matcher(text);
            StringBuffer result = new StringBuffer();
            while (matcher.find()) {
                String match = matcher.group();
                String digitsOnly = match.replaceAll("[^0-9A-Za-z]", "");
                int len = digitsOnly.length();
                if (len <= 4) {
                    matcher.appendReplacement(result, repeat('*', len));
                    continue;
                }
                int maskedCount = len - 4;
                StringBuilder masked = new StringBuilder();
                for (int i = 0; i < maskedCount; i++) {
                    masked.append('*');
                }
                masked.append(digitsOnly.substring(maskedCount));
                matcher.appendReplacement(result, masked.toString());
            }
            matcher.appendTail(result);
            return result.toString();
        }

        private static String repeat(char c, int times) {
            StringBuilder sb = new StringBuilder();
            for (int i = 0; i < times; i++) {
                sb.append(c);
            }
            return sb.toString();
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            RedactionForm frame = new RedactionForm();
            frame.setVisible(true);
        });
    }
}
