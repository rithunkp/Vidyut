import java.io.*;
import java.nio.file.*;
import java.util.regex.*;

public class RedactionTool {

    // Regex patterns for sensitive data
    private static final String EMAIL_REGEX = "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b";
    private static final String PHONE_REGEX = "\\b(\\+\\d{1,3}[- ]?)?\\d{10}\\b";
    
    // Credit card: 13 to 19 digits, allowing spaces or dashes
    private static final String CREDIT_CARD_REGEX = "\\b(?:\\d[ -]*?){13,19}\\b";

    // Passport: Assume 1 letter + 7 digits OR 9 alphanumeric characters (simple generic pattern)
    private static final String PASSPORT_REGEX = "\\b([A-Za-z]\\d{7}|[A-Za-z0-9]{9})\\b";

    // Resident ID (like Aadhaar): exactly 12 digits
    private static final String RESIDENT_ID_REGEX = "\\b\\d{12}\\b";

    // Bank Account: 8 to 14 digits
    private static final String BANK_ACCOUNT_REGEX = "\\b\\d{8,14}\\b";

    public static void main(String[] args) {
        if (args.length < 2) {
            System.out.println("Usage: java RedactionTool <inputFilePath> <outputFilePath>");
            return;
        }

        String inputPath = args[0];
        String outputPath = args[1];

        try {
            String content = new String(Files.readAllBytes(Paths.get(inputPath)));
            String redactedContent = redactSensitiveData(content);
            Files.write(Paths.get(outputPath), redactedContent.getBytes());
            System.out.println("Redacted file saved to: " + outputPath);
        } catch (IOException e) {
            System.err.println("Error processing file: " + e.getMessage());
        }
    }

    private static String redactSensitiveData(String text) {
        // Mask phone numbers: first 5 digits '*'
        text = maskPhoneNumbers(text);

        // Mask emails: all chars before '@' replaced with '*'
        text = maskEmails(text);

        // Mask credit card numbers: replace all digits but last 4 with '*'
        text = maskGenericNumber(text, CREDIT_CARD_REGEX);

        // Mask passport numbers similarly
        text = maskGenericNumber(text, PASSPORT_REGEX);

        // Mask resident ID (12 digits)
        text = maskGenericNumber(text, RESIDENT_ID_REGEX);

        // Mask bank account numbers
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

            // Remove spaces/dashes for masking but keep original format for replacement
            String digitsOnly = match.replaceAll("[^0-9A-Za-z]", "");

            int len = digitsOnly.length();
            if (len <= 4) {
                // If very short, mask fully
                matcher.appendReplacement(result, repeat('*', len));
                continue;
            }

            int unmaskedCount = 4;
            int maskedCount = len - unmaskedCount;

            StringBuilder masked = new StringBuilder();

            // For masking, mask first maskedCount chars, then add last 4 chars
            for (int i = 0; i < maskedCount; i++) {
                masked.append('*');
            }
            masked.append(digitsOnly.substring(maskedCount));

            // Now we need to re-insert the original formatting (spaces/dashes) if any
            // Simple approach: just replace whole match with masked string (without formatting)
            matcher.appendReplacement(result, masked.toString());
        }
        matcher.appendTail(result);
        return result.toString();
    }

    private static String repeat(char c, int times) {
        StringBuilder sb = new StringBuilder();
        for (int i=0; i < times; i++) {
            sb.append(c);
        }
        return sb.toString();
    }
}
