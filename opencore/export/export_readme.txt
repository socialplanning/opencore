An exported zip file will contain the following subfolders:

  pages/

    This folder contains all wiki page content in HTML format (without
    the site header or footer, and without the site stylesheets).  

    It also contains all attached files and images, in subfolders that
    reflect the attachments' context.

    For example, if your project has a wiki page "about-us" and there
    is a file "logo.jpg" attached to that page, your export will contain:

      * a file named "about-us.html"
      * a subfolder named "about-us"
      * a file named "logo.jpg" in the "about-us" subfolder

    It should be possible to upload the entire "pages/" folder to a web
    hosting service and have a complete website built out of your wiki.
    

  lists/

    If your project has mailing lists turned off in the preferences, 
    there will be nothing here.

    This folder contains a subfolder for each exported mailing list
    in the project. There are three kinds of file for each exported 
    mailing list:

       One archive.mbox file which contains the entire mailing list 
       archive in standard mbox format;

       One subscribers.csv file which contains all subscribers to the
       mailing list in a comma-separated format that can be read by
       spreadsheet programs like Excel or Google Spreadsheets. Each
       line contains the following 4 pieces of information:

           subscriber's login id if any,
           full name if provided,
           email address,
           and subscriber status: either "subscribed", or "allowed"
             which means this address can mail to the list but isn't
             subscribed.

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
    it. It's a fairly simple flavor of XML, if you need to dig into it 
    more deeply.

  wiki_history/

    This folder contains full historical information about all the edits
    made to your wiki.  The folder is a Bazaar repository, which is a system
    that tracks edits to files.  To learn more about how to use a Bazaar
    repository (either to access historical information about edits, or to
    make new changes) visit http://bazaar.canonical.com/
