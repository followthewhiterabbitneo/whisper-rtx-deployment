#!/usr/bin/env python3
"""
Create a realistic test transcript for Eric Rawlins loan call
"""

transcript_content = """TRANSCRIPT - Call Recording
Date: June 20, 2025 14:56:45
Duration: 197 seconds
Participant: Eric Rawlins
Reference: 20250620_145645_LOLW

[Agent] Good afternoon, Shore Mortgage customer service, this is Sarah speaking. How may I assist you today?

[Eric Rawlins] Hi Sarah, this is Eric Rawlins. I'm calling to check on the status of my loan modification application.

[Agent] I'd be happy to help you with that, Mr. Rawlins. May I have your loan number please?

[Eric Rawlins] Yes, it's 4521887.

[Agent] Thank you. Let me pull up your account... Alright, I see here that you submitted your loan modification application on June 1st, 2025. Is that correct?

[Eric Rawlins] Yes, that's right. I sent in all the documents you requested.

[Agent] Perfect. I can see that we received your complete application package including your hardship letter, proof of income, bank statements for the last three months, and your most recent tax returns.

[Eric Rawlins] Good. So what's the status? I'm getting worried because my next payment is due soon.

[Agent] I understand your concern, Mr. Rawlins. Your application is currently with our underwriting department for review. The good news is that it's moving through the process. Our standard timeline is 7 to 10 business days from receipt of a complete application.

[Eric Rawlins] So when should I expect to hear something?

[Agent] Based on when we received your complete package, you should receive a decision by June 14th or 15th at the latest. We'll contact you by phone and send a written decision letter as well.

[Eric Rawlins] What about my upcoming payment? Should I make it while this is being reviewed?

[Agent] That's a great question. While your modification is under review, we do recommend continuing to make payments if you're able to. However, I see you mentioned financial hardship in your application. Would you like me to look into our forbearance options?

[Eric Rawlins] Yes, please. I'm not sure I can make the full payment this month.

[Agent] Certainly. We have a temporary payment suspension program that might help. You can apply for this online through your account portal, or I can send you the application via email. This would allow you to pause or reduce payments for up to three months while your modification is being processed.

[Eric Rawlins] That would be very helpful. Can you email me that information?

[Agent] Absolutely. I'll send that to the email address we have on file, which ends in @gmail.com. Is that still correct?

[Eric Rawlins] Yes, that's correct.

[Agent] Perfect. You should receive that within the next hour. The application is straightforward, but if you have any questions, please don't hesitate to call us back.

[Eric Rawlins] Thank you. One more thing - if my modification is approved, when would the new terms take effect?

[Agent] If approved, the new terms would typically take effect with your next billing cycle after approval. We'll provide you with a modified loan agreement that details your new payment amount, interest rate, and any other changed terms.

[Eric Rawlins] Okay, that makes sense. Is there anything else I need to do right now?

[Agent] No, Mr. Rawlins. We have everything we need. Just watch for our decision letter and feel free to complete that forbearance application if you need temporary relief. Your reference number for today's call is SR-2025-0620-3847.

[Eric Rawlins] Thank you so much for your help, Sarah.

[Agent] You're very welcome, Mr. Rawlins. We appreciate your patience during this process. Have a great day.

[Eric Rawlins] You too. Goodbye.

[Agent] Goodbye.

[END OF TRANSCRIPT]
"""

# Save the transcript
with open('/moneyball/whisper-rtx-deployment/eric_rawlins_transcript.txt', 'w') as f:
    f.write(transcript_content)

print("Created test transcript: /moneyball/whisper-rtx-deployment/eric_rawlins_transcript.txt")
print(f"Length: {len(transcript_content)} characters")
print("\nFirst 200 characters:")
print(transcript_content[:200] + "...")