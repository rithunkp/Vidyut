import java.io.*;
import java.nio.file.*;
import java.util.regex.*;

public class RedactionTool {

    private static final String EMAIL_REGEX = "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b";
    private static final String PHONE_REGEX = "\\b(\\+\\d{1,3}[- ]?)?\\d{10}\\b";
    private static final String CREDIT_CARD_REGEX = "\\b(?:\\d[ -]*?){13,19}\\b";
    private static final String PASSPORT_REGEX = "\\b([A-Za-z]\\d{7}|[A-Za-z0-9]{9})\\b";
    private static final String NUMBER_REGEX = "\\b\\d{8,14}\\b";

    public static void main(String[] args) {
        if (args.length < 2) {
            System.out.println("Usage: java RedactionTool <inputFilePath> <outputFilePath>");
            return;
        }

        String inputPath = args[0];
        String outputPath = args[1];

        try {
            String content = new String(Files.readAllBytes(Paths.get(inputPath)));
            String redactedContent = redactdata(content);
            Files.write(Paths.get(outputPath), redactedContent.getBytes());
            System.out.println("Redacted file saved to: " + outputPath);
        } catch (IOException e) {
            System.err.println("Error processing file: " + e.getMessage());
        }
    }

    private static String redactdata(String text) {
        // first 5 digits '*'
        text = rphone(text);
        // all chars before '@' replaced with '*'
        text = rmail(text);
        // all digits but last 4 with '*'
        text = rno(text, CREDIT_CARD_REGEX);
        text = rno(text, PASSPORT_REGEX);
        text = rno(text, NUMBER_REGEX);
        return text;
    }

    private static String rphone(String text) {
        Pattern pattern = Pattern.compile(PHONE_REGEX);
        Matcher matcher = pattern.matcher(text);
        StringBuffer result = new StringBuffer();
        while (matcher.find()) {
            String phone = matcher.group();
            StringBuilder masked = new StringBuilder();
            int n = 0;
            for (char c : phone.toCharArray()) {
                if (Character.isDigit(c) && n < 5) {
                    masked.append('*');
                    n++;
                } else {
                    masked.append(c);
                }
            }
            matcher.appendReplacement(result, masked.toString());
        }
        matcher.appendTail(result);
        return result.toString();
    }

    private static String rmail(String text) {
        Pattern pattern = Pattern.compile(EMAIL_REGEX);
        Matcher matcher = pattern.matcher(text);
        StringBuffer result = new StringBuffer();
        while (matcher.find()) {
            String email = matcher.group();
            int index = email.indexOf('@');
            if (index > 0) {
                StringBuilder masked = new StringBuilder();
                for (int i = 0; i < index; i++) {
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

    private static String rno(String text, String regex) {
        Pattern pattern = Pattern.compile(regex);
        Matcher matcher = pattern.matcher(text);
        StringBuffer result = new StringBuffer();
        while (matcher.find()) {
            String match = matcher.group();
            String digits = match.replaceAll("[^0-9A-Za-z]", "");

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

    private static String repeat(char c, int times) {
        StringBuilder sb = new StringBuilder();
        for (int i=0; i < times; i++) {
            sb.append(c);
        }
        return sb.toString();
    }
}
