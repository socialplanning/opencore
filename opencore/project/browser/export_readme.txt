An exported zip file will contain the following subfolders:

  pages/

    This folder contains all wiki page content in HTML format (without
    the site header or footer, and without the site stylesheets).  

    It also contains all attached files and images.

    Historical versions of wiki pages are currently not included in
    the export.

  lists/

    This folder contains a subfolder for each exported mailing list
    in the project. There are three kinds of file for each exported 
    mailing list:

       One archive.mbox file which contains the entire mailing list 
       archive in standard mbox format;

       One subscribers.csv file which contains all subscribers to the
       mailing list in a comma-separated format. Each line contains
       the following 4 pieces of information:

           subscriber's login id if any,
           full name if provided,
           email address,
           and subscriber status (either "subscribed", or "allowed"
             which means this address can mail to the list but isn't subscribed.

       One settings.ini file which contains the settings and preferences
       for the mailing list, including things like its title, description,
       mailing address; a list of the usernames of all list managers;
       and the moderation policy and archival policy.
  
  blog/

    If your project has blogs turned off in the preferences, there
    will be nothing here.

    If you have blogs turned on, this folder contains an export of all
    posts and comments on your blog. It also contains blog categories
    and tags, and any blogroll entries you have.

    It is saved in Wordpress' usual Extended RSS (WXR) format, which 
    doesn't seem to be documented anywhere, but Wordpress can import
    it, and many other popular blogging platforms can import it too.
    It's a fairly simple flavor of XML, if you need to dig into it 
    more deeply.

