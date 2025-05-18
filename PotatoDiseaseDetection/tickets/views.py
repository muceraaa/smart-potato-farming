from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail, EmailMessage  # for sending emails
from django.db.models import Q
from django.shortcuts import get_object_or_404, render, redirect
from .models import *
from .forms import *
import datetime  # for the accepted time for the ticket
from django.http import JsonResponse
import openai
from typing import Optional, List



from .templates.ai.predict import predict_issue
from .templates.ai.pr import predict_single_image
from .templates.ai.predict1 import predict_and_display

# home view
def home(request):
    """
    Logic for the home view
    """
    tickets = Ticket.objects.all()

    context = {'tickets': tickets}
    return render(request, 'tickets/home.html', context)

def contact(request):
    """
    logic for the contact page
    """

    if request.method == 'POST':
        sender_name = request.POST.get('sender-name', '')
        sender_email = request.POST.get('sender-email', '')
        message_title = request.POST.get('message-title', '')
        message_body = request.POST.get('message-body', '')

        send_mail (
            message_title,
            message_body,
            sender_email,
            ['muceraaa@gmail.com'],
        )
        messages.success(request, f'The message has been sent. We will get back to you\
                         as soon as possible!')
        return redirect('contact')
    
    return render(request, 'tickets/contact.html')

def predictionView(request):
    """
    logic for the contact page
    """

    # if request.method == 'POST':
    #     sender_name = request.POST.get('sender-name', '')
    #     sender_email = request.POST.get('sender-email', '')
    #     message_title = request.POST.get('message-title', '')
    #     message_body = request.POST.get('message-body', '')
    #
    #     send_mail (
    #         message_title,
    #         message_body,
    #         sender_email,
    #         ['muceraaa@gmail.com'],
    #     )
    #     messages.success(request, f'The message has been sent. We will get back to you\
    #                      as soon as possible!')
    #     return redirect('contact')

    return render(request, 'tickets/prediction-view.html')

def ticketsView(request):
    """
    Logic for the tickets page
    Has search functionality enabling user to search a
    ticket by title, description status, who ticket is assigned_to
    and created_by
    """
    tickets = Ticket.objects.all()
    status = request.GET.get('status')  # to filter by status
    query = request.GET.get('q')  # search parameter

    if status:
        tickets = Ticket.objects.filter(status=status)

    elif query:
        tickets = tickets.filter(
            Q(title__icontains=query) |  # Case-insensitive search in title
            Q(description__icontains=query) |
            Q(status__icontains=query) |
            Q(created_by__username__icontains=query) |
            Q(assigned_to__username__icontains=query)
        )

    tickets = tickets.order_by('-status', '-created_on')
    # Get the counts for each status
    all_count = Ticket.objects.count()
    open_count = Ticket.objects.filter(status='open').count()
    active_count = Ticket.objects.filter(status='active').count()
    closed_count = Ticket.objects.filter(status='closed').count()

    context = {
        'tickets': tickets,
        'open_count': open_count,
        'active_count': active_count,
        'closed_count': closed_count,
        'all_count': all_count,
        'selected_status': status
    }
    return render(request, 'tickets/tickets-view.html', context)

@login_required(login_url=('account_login'))
def ticketDetails(request, slug):
    """
    Logic for the ticket detail page.
    Users can send messages within this view.
    Args:
        slug: the ticket slug
    """
    ticket = Ticket.objects.get(slug=slug)
    msg = ticket.messages.all().order_by('sent_on')  # msg = messages

    if request.method == 'POST':
        # Create the new message
        ticket_message = TicketMessage.objects.create(
            sender=request.user,
            ticket=ticket,
            message=request.POST.get('message')
        )

        # Find the assigned engineer
        assigned_engineer = ticket.assigned_to

        # Handle the case where the ticket is not assigned to any engineer
        if assigned_engineer is None:
            # Optionally, you can add a message to inform the user
            messages.warning(request, 'This ticket is not assigned to any engineer.')
            return redirect('ticket-details', slug=slug)

        # If the assigned engineer is AI, predict the solution
        if assigned_engineer.username == 'ai':
            example_desc = ticket.description


            print("description being used", example_desc)
            pred_category, pred_urgency, pred_time, pred_solution = predict_issue(example_desc)

            print("Predicted solution", pred_solution)
            # print(pred_urgency)

            # Create a message from the AI with the predicted solution
            TicketMessage.objects.create(
                sender=assigned_engineer,
                ticket=ticket,
                message=f"{pred_solution}"
            )
            # add urgency and resolution time to the ticket
            ticket.urgency = pred_urgency
            print(
                f"Predicted Category: {pred_category}, Urgency: {pred_urgency}, Resolution Time: {pred_time} mins, Suggested Solution: {pred_solution}")

        return redirect('ticket-details', slug=slug)

    context = {
        'ticket': ticket,
        'msg': msg,
    }
    return render(request, 'tickets/ticket-details.html', context)

@login_required(login_url=('account_login'))
def deleteTicket(request, slug):
    """
    Logic for deleting a ticket
    """
    ticket = get_object_or_404(Ticket, slug=slug)

    # only created_by and assigne_by can delete the ticket
    if request.user != ticket.created_by and request.user != ticket.assigned_to:
        messages.warning(request, f'You do not have permission to delete this ticket!')
        if request.user.user_type == 'client':
            return redirect('client-dashboard', username=request.user.username)
        elif request.user.user_type == 'engineer':
            return redirect('engineer-dashboard', username=request.user.username)
        else:
            return redirect('home')

    if request.method == 'POST':
        ticket.delete()
        messages.success(request, f'Ticket has been delete!')

        # client redirected to their dashboard, same as engineer
        if request.user.user_type == 'client':
            return redirect('client-dashboard', username=request.user.username)
        elif request.user.user_type == 'engineer':
            return redirect('engineer-dashboard', username=request.user.username)
        else:
            return redirect('home')

    context = { 'obj': ticket }
    return redirect(request, 'tickets/delete.html', context)


@login_required(login_url=('account_login'))
def deleteMessage(request, msgId):
    """
    Logic for deleting a message within the detailed view
    Args:
        msgId: The id of the message to be deleted
    """
    message = get_object_or_404(TicketMessage, pk=msgId)

    if request.method == 'POST':
        if request.user == message.sender:
            message.delete()
            messages.success(request, f'The message has been deleted')
            return redirect('ticket-details', slug=message.ticket.slug)
        else:
            messages.warning(request, f'You do not have permission to delete this message!')
            return redirect('ticket-details', slug=message.ticket.slug)
        
    
    return render(request, 'tickets/delete.html', {'obj': message})

# <==================== Clientss views ====================>
@login_required(login_url=('account_login'))
def clientDashboard(request, username):
    """
    logic for a dashboard that shows all the tickets a client has
    Creates on
    Args:
        username: the request user who is a client
    """
    current_client = get_object_or_404(CustomUser, username=username)
    tickets = Ticket.objects.filter(created_by=current_client)
    status = request.GET.get('status')
    query = request.GET.get('Q')

    if status:
        tickets = Ticket.objects.filter(status=status)

    elif query:
        tickets = tickets.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(status__icontains=query) |
            Q(assigned_to__username__icontains=query)
        )

    tickets = tickets.order_by('-status', '-created_on')
    # Get the relative counts for the dashboard
    all_count = tickets.count()
    active_count = tickets.filter(status='active').count()
    closed_count = tickets.filter(status='closed').count()

    context = {
        'tickets': tickets,
        'all_count': all_count,
        'active_count': active_count,
        'closed_count': closed_count,
        }

    return render(request, 'tickets/client-dashboard.html', context)

@login_required(login_url=('account_login'))
def updateTicket(request, slug):
    """
    logic for updating a ticket
    """
    ticket = get_object_or_404(Ticket, slug=slug)

    # check if request.user is the one who created the ticket
    if request.user != ticket.created_by:
        messages.error(request, f'You do not have permission to update this ticket')
        return redirect('ticket-details')
    
    if request.method == 'POST':
        form = NewTicketForm(request.POST, request.FILES, instance=ticket)
        if form.is_valid():
            form.save()
            messages.success(request, f'Your ticket has been updated')
            return redirect ('client-dashboard', username=request.user)
        
        else:
            messages.error(request, f'Something went wrong. Check your inputs and try again')

    else:    
        form = NewTicketForm(instance=ticket)

    context = {'form': form}

    return render(request, 'tickets/update-ticket.html', context)




def get_title(
    description: str,
    api_key: str,
    tone: str = "creative",
    keywords: Optional[List[str]] = None,
    model: str = "gpt-3.5-turbo",
    max_tokens: int = 30,
    temperature: float = 0.7
) -> str:
    # Validate inputs
    if not api_key.startswith('sk-'):
        raise ValueError("Invalid OpenAI API key format")
    
    if not description.strip():
        raise ValueError("Description cannot be empty")

    # Construct the prompt
    prompt_parts = [
        f"Generate a {tone} title for this content:",
        f"Description: {description}",
    ]
    
    if keywords:
        prompt_parts.append(f"Keywords to include: {', '.join(keywords)}")
    
    prompt_parts.append("Suggested title:")
    prompt = "\n".join(prompt_parts)

    try:
        # Configure API
        openai.api_key = api_key
        
        # Make the API call
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a world-class copywriter."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Extract and clean the title
        title = response.choices[0].message.content.strip()
        title = title.split('\n')[0]  # Take first line if multiple
        title = title.strip('"\'')  # Remove wrapping quotes
        
        return title

    except Exception as e:
        raise ValueError(f"API request failed: {str(e)}")


def _get_title(description: str, tone="creative", keywords: Optional[List[str]] = None):
    print(description)
    API_KEY = "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"  # Never commit real keys to code!
    
    example_desc = (
        "A thrilling sci-fi adventure about a rogue AI that gains consciousness "
        "and must choose between humanity's survival or its own evolution."
    )
    
    try:
        title = get_title(
            description=example_desc,
            api_key=API_KEY,
            tone="dramatic",
            keywords=["AI", "future"],
            model="gpt-3.5-turbo"
        )
        print(f"Generated title: {title}")
        
    except ValueError as e:
        print(f"Error: {e}")
    prompt = f"""
    Generate a compelling title based on the following description. 
    Tone: {tone}.
    {f"Keywords to include: {', '.join(keywords)}." if keywords else ""}
    
    Description:
    {description}
    
    Possible Titles:
    1. 
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-4",  # or "gpt-3.5-turbo"
        messages=[
            {"role": "system", "content": "You are a creative assistant that generates engaging titles."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=50,
        temperature=0.7  # Adjust for creativity (higher = more random)
    )
    
    # Extract the first suggested title
    title = response.choices[0].message.content.strip().split("\n")[0]
    print(f"Generated Title: {title}")
    return title




# openai.api_key = '2IboGQ7nKblGmx7FChKsL3k8BOlmnS8yC79woaNGnRtuYmL1N6q9JQQJ99BDACfhMk5XJ3w3AAABACOGhCT3'  # Replace with your actual API key


from openai import AzureOpenAI

# Azure configuration
endpoint = "https://api-key1.openai.azure.com/"
deployment = "gpt-4o"  # Your deployment name
api_version = "2024-12-01-preview"
subscription_key = "2IboGQ7nKblGmx7FChKsL3k8BOlmnS8yC79woaNGnRtuYmL1N6q9JQQJ99BDACfhMk5XJ3w3AAABACOGhCT3"  # Replace with your Azure OpenAI key

# Create client
client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=subscription_key,
)


def ask_openai_about_disease_issue_azure(disease, confidence, description):
    """
    Uses Azure OpenAI to ask about a plant disease issue, and returns a 10-line summary.
    """
    prompt = f"""
    A plant image was analyzed and the AI predicted the disease is '{disease}' with {confidence}% confidence.

    The user also provided this description:
    "{description}"

    Based on this, provide:
    - A diagnosis (if appropriate)
    - Recommended treatment or next steps
    - Advice for the user on how to handle the issue

    ❗Return the response in **no more than 10 lines**.
    Be concise, practical, and use clear language.
    """

    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system",
                 "content": "You are an expert plant pathologist helping users diagnose and solve crop issues."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=700,
            temperature=0.7,
            top_p=1.0,
            model=deployment
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print("Error contacting Azure OpenAI:", e)
        return "Sorry, we could not generate a response at this time."


@login_required(login_url=('account_login'))
def createTicket(request):
    """
    Logic for creating a new ticket
    """
    if request.method == 'POST':
        form = NewTicketForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by = request.user
            ticket.save()

            
            example_desc = ticket.description

            # example_title = _get_title(example_desc)
            example_title = ticket.title

            if (ticket.image_reference):
                reference_prediction = UploadedImage.objects.get(id=ticket.image_reference.id)

                pred_category = reference_prediction.disease
                pred_urgency, pred_time = 1, 5
                pred_solution = ask_openai_about_disease_issue_azure(reference_prediction.disease, reference_prediction.accuracy, example_desc)
                print("Predicted solution", pred_solution)


            else:
                pred_category, pred_urgency, pred_time, pred_solution = predict_issue(example_desc)




            ai_engineer = CustomUser.objects.get(username='ai')

            ticket.status = 'active'
            ticket.assigned_to = ai_engineer
            ticket.accepted_on = datetime.datetime.now()

            ticket.save()
            ticket_message = TicketMessage.objects.create(
                sender=ai_engineer,
                ticket=ticket,
                message=f"{pred_solution}"
            )

            print(f"Predicted Category: {pred_category}, Urgency: {pred_urgency}, Resolution Time: {pred_time} mins, Suggested Solution: {pred_solution}")

            return redirect('ticket-details', slug=ticket.slug)
    else:
        form = NewTicketForm(user=request.user)
    return render(request, 'tickets/create-ticket.html', {'form': form})


@login_required(login_url=('account_login'))
def uploadImage(request):
    if request.method == 'POST':
        user = request.user

        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Create object but don't commit yet
            instance = form.save(commit=False)
            instance.created_by = user

            # Save the image file first so we can access .path
            instance.save()

            # Now you can safely access image.path
            image_path = instance.image.path

            # Call your prediction function
            predicted_class, confidence_score = predict_and_display(image_path)

            # Update instance with prediction and confidence
            instance.disease = predicted_class
            instance.accuracy = round(float(confidence_score), 2)*100
            instance.save()

            return JsonResponse({
                'prediction': predicted_class,
                'confidence': round(float(confidence_score), 2)*100,
                'image': instance.image.url
            })
    else:
        form = ImageUploadForm()

    return render(request, 'tickets/create-ticket.html', {'form': form})



@login_required(login_url=('account_login'))
def submit_rating(request, ticket_id):
    try:
        ticket = Ticket.objects.get(id=ticket_id)
        rating = int(request.POST.get('rating', 0))

        if 1 <= rating <= 5:
            ticket.rating = rating
            ticket.save()
            return JsonResponse({'status': 'success', 'message': 'Rating submitted successfully.'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid rating value.'}, status=400)
    except Ticket.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Ticket not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)



@login_required(login_url=('account_login'))
def escalateTicket(request, ticket_id):
    try:
        ticket = Ticket.objects.get(id=ticket_id)
        if ticket.assigned_to is None:
            return JsonResponse({'status': 'error', 'message': 'Ticket is not assigned to any engineer.'}, status=400)
        ticket.assigned_to = None
        ticket.status = 'open'
        ticket.save()
        return JsonResponse({'status': 'success', 'message': 'Ticket escalated successfully.'})
    except Ticket.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Ticket not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)



# <==================== Engineers views ====================>

@login_required(login_url=('account_login'))
def acceptTicket(request, slug):
    """
    logic for engineer accepting a ticket
    Args:
        slug: the slug of the ticket
    """
    ticket = get_object_or_404(Ticket, slug=slug)

    if request.user.user_type == 'engineer':
    
        ticket.status = 'active'
        ticket.assigned_to = request.user
        ticket.accepted_on = datetime.datetime.now()
        ticket.save()
    # else:
    #     messages.warning(request, f'Only engineers can accept a ticket!')
    #     return redirect('ticket_details', slug=slug)

    return redirect('ticket-details', slug=slug)

@login_required(login_url=('account_login'))
def closeTicket(request, slug):
    """
    logic for closing a ticket by the accepted engineer when it is resolved
    Args:
        slug: the ticket slug
    """
    ticket = get_object_or_404(Ticket, slug=slug)

    if request.user == ticket.assigned_to:
        ticket.status = 'closed'
        ticket.closed_on = datetime.datetime.now()
        ticket.save()

    return redirect('tickets-view')

@login_required(login_url=('account_login'))
def engineerDashboard(request, username):
    """
    logic for a dashboard that shows all the tickets an engineer has
    worked on
    Args:
        user: the request user who is an engineer
    """
    current_engineer = get_object_or_404(CustomUser, username=username)
    tickets = Ticket.objects.filter(assigned_to=current_engineer)
    status = request.GET.get('status')
    query = request.GET.get('Q')

    if status:
        tickets = Ticket.objects.filter(status=status)

    elif query:
        tickets = tickets.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(status__icontains=query) |
            Q(created_by__username__icontains=query)
        )

    tickets = tickets.order_by('-status', '-created_on')
    # Get the relative counts for the dashboard
    all_count = tickets.count()
    active_count = tickets.filter(status='active').count()
    closed_count = tickets.filter(status='closed').count()

    context = {
        'tickets': tickets,
        'all_count': all_count,
        'active_count': active_count,
        'closed_count': closed_count,
        }

    return render(request, 'tickets/engineer-dashboard.html', context)
