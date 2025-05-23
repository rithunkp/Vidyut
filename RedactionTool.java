import java.io.*;
import java.nio.file.*;
import java.util.regex.*;

public class RedactionTool {

    // Patterns for sensitive information
    private static final String EMAIL_REGEX = "\\b[A-Za-z0-9]([A-Za-z0-9._%-]*[A-Za-z0-9])?@[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?\\.[A-Za-z]{2,}\\b";
    private static final String PHONE_REGEX = "\\b(?:\\+?1[-\\s]?)?\\(?[0-9]{3}\\)?[-\\s]?[0-9]{3}[-\\s]?[0-9]{4}\\b|\\b\\+\\d{1,3}[-\\s]?\\d{1,4}[-\\s]?\\d{1,4}[-\\s]?\\d{1,9}\\b";
    private static final String CREDIT_CARD_REGEX = "\\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\\b|\\b(?:[0-9]{4}[-\\s]){3}[0-9]{4}\\b|\\b[0-9]{13,19}\\b";
    private static final String PASSPORT_REGEX = "\\b[A-Z][0-9]{8}\\b|\\b[A-Z]{2}[0-9]{7}\\b";
    private static final String SSN_REGEX = "\\b[0-9]{3}-[0-9]{2}-[0-9]{4}\\b";
    private static final String BANK_ACCOUNT_REGEX = "\\b[0-9]{8,17}\\b(?=\\s|$|[^A-Za-z0-9])";

    public static void main(String[] args) {
        if (args.length < 2) {
            System.out.println("Usage: java RedactionTool <inputFilePath> <outputFilePath>");
            return;
        }

        String inputPath = args[0];
        String outputPath = args[1];

        try {
            // Read the file
            String content = new String(Files.readAllBytes(Paths.get(inputPath)));
            
            // Hide sensitive stuff
            String redactedContent = redactdata(content);
            
            // Save the cleaned file
            Files.write(Paths.get(outputPath), redactedContent.getBytes());
            System.out.println("Redacted file saved to: " + outputPath);
        } catch (IOException e) {
            System.err.println("Error processing file: " + e.getMessage());
        }
    }

    // Hide all the sensitive stuff
    private static String redactdata(String text) {
        text = rphone(text);
        text = rmail(text);
        text = redactSSN(text);
        text = rno(text, CREDIT_CARD_REGEX);
        text = rno(text, PASSPORT_REGEX);
        text = redactBankAccount(text);
        return text;
    }

    // Hide phone numbers
    private static String rphone(String text) {
        Pattern pattern = Pattern.compile(PHONE_REGEX);
        Matcher matcher = pattern.matcher(text);
        StringBuffer result = new StringBuffer();
        while (matcher.find()) {
            String phone = matcher.group();
            String digitsOnly = phone.replaceAll("[^0-9]", "");
            
            // Make sure it's actually a phone number
            if (digitsOnly.length() >= 10 && digitsOnly.length() <= 15) {
                StringBuilder masked = new StringBuilder();
                int digitCount = 0;
                for (char c : phone.toCharArray()) {
                    if (Character.isDigit(c) && digitCount < 6) {
                        masked.append('*');
                        digitCount++;
                    } else {
                        masked.append(c);
                    }
                }
                matcher.appendReplacement(result, masked.toString());
            } else {
                matcher.appendReplacement(result, phone);
            }
        }
        matcher.appendTail(result);
        return result.toString();
    }

    // Hide email addresses
    private static String rmail(String text) {
        Pattern pattern = Pattern.compile(EMAIL_REGEX);
        Matcher matcher = pattern.matcher(text);
        StringBuffer result = new StringBuffer();
        while (matcher.find()) {
            String email = matcher.group();
            int index = email.indexOf('@');
            if (index > 0) {
                StringBuilder masked = new StringBuilder();
                masked.append(email.charAt(0));
                for (int i = 1; i < index; i++) {
                    masked.append('*');
                }
                masked.append(email.substring(index));
                matcher.appendReplacement(result, masked.toString());
            } else {
                matcher.appendReplacement(result, email);
            }
        }
        matcher.appendTail(result);
        return result.toString();
    }

    // Hide Social Security Numbers
    private static String redactSSN(String text) {
        Pattern pattern = Pattern.compile(SSN_REGEX);
        Matcher matcher = pattern.matcher(text);
        StringBuffer result = new StringBuffer();
        while (matcher.find()) {
            matcher.appendReplacement(result, "***-**-****");
        }
        matcher.appendTail(result);
        return result.toString();
    }

    // Hide bank account numbers
    private static String redactBankAccount(String text) {
        Pattern pattern = Pattern.compile(BANK_ACCOUNT_REGEX);
        Matcher matcher = pattern.matcher(text);
        StringBuffer result = new StringBuffer();
        while (matcher.find()) {
            String match = matcher.group();
            String digitsOnly = match.replaceAll("[^0-9]", "");
            
            if (digitsOnly.length() >= 8 && digitsOnly.length() <= 17) {
                String masked = "****" + digitsOnly.substring(digitsOnly.length() - 4);
                matcher.appendReplacement(result, masked);
            } else {
                matcher.appendReplacement(result, match);
            }
        }
        matcher.appendTail(result);
        return result.toString();
    }

    // Hide credit cards and passports
    private static String rno(String text, String regex) {
        Pattern pattern = Pattern.compile(regex);
        Matcher matcher = pattern.matcher(text);
        StringBuffer result = new StringBuffer();
        while (matcher.find()) {
            String match = matcher.group();
            String digits = match.replaceAll("[^0-9A-Za-z]", "");

            // Check if it's a real credit card
            if (regex.equals(CREDIT_CARD_REGEX)) {
                String numbersOnly = match.replaceAll("[^0-9]", "");
                if (numbersOnly.length() < 13 || numbersOnly.length() > 19) {
                    matcher.appendReplacement(result, match);
                    continue;
                }
                if (!isValidCreditCard(numbersOnly)) {
                    matcher.appendReplacement(result, match);
                    continue;
                }
            }

            int len = digits.length();
            if (len <= 4) {
                matcher.appendReplacement(result, repeat('*', len));
                continue;
            }

            int n = 4;
            int m = len - n;
            StringBuilder masked = new StringBuilder();
            for (int i = 0; i < m; i++) {
                masked.append('*');
            }
            masked.append(digits.substring(m));
            matcher.appendReplacement(result, masked.toString());
        }
        matcher.appendTail(result);
        return result.toString();
    }

    // Check if credit card number is real
    private static boolean isValidCreditCard(String number) {
        int sum = 0;
        boolean alternate = false;
        for (int i = number.length() - 1; i >= 0; i--) {
            int digit = Character.getNumericValue(number.charAt(i));
            if (alternate) {
                digit *= 2;
                if (digit > 9) {
                    digit = (digit % 10) + 1;
                }
            }
            sum += digit;
            alternate = !alternate;
        }
        return (sum % 10 == 0);
    }

    // Make multiple stars
    private static String repeat(char c, int times) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < times; i++) {
            sb.append(c);
        }
        return sb.toString();
    }
}