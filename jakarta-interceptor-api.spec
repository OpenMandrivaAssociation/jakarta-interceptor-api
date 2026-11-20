Name:		jakarta-interceptor-api
Version:	2.2.0
Release:	1
Summary:	Jakarta Interceptors API
Group:		Development/Java
License:	EPL-2.0 OR GPL-2.0-only WITH Classpath-exception-2.0
URL:		https://github.com/jakartaee/interceptors
Source0:	https://github.com/jakartaee/interceptors/archive/refs/tags/%{version}-RELEASE.tar.gz#/jakarta-interceptor-api-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar
BuildRequires:	jakarta-annotation-api >= 3.0.0
Requires:	jakarta-annotation-api >= 3.0.0

%{!?annotation_api:%global annotation_api %{_javadir}/jakarta.annotation-api.jar}

%description
Jakarta Interceptors API 2.2.0, coordinate
jakarta.interceptor:jakarta.interceptor-api. The classes live in
jakarta.interceptor. jboss-interceptors-1.2-api remains the
javax.interceptor jar. The upstream POM depends on Jakarta Annotations
3.0.0. The 2.2.0-RELEASE tag still writes 2.2.1-SNAPSHOT into its
reactor POM; this package publishes the released coordinate 2.2.0.

%prep
%autosetup -n interceptors-%{version}-RELEASE -p1
find . \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -delete
python - << 'PY'
from pathlib import Path
files = [path for path in Path("api/src/main/java").rglob("*.java") if path.name != "module-info.java"]
if len(files) != 9:
    raise SystemExit("interceptor sources " + str(len(files)))
PY

%build
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
mkdir -p classes
find api/src/main/java -name '*.java' ! -name module-info.java > sources.list
test "$(wc -l < sources.list)" -eq 9
javac --release 8 -encoding UTF-8 -Xlint:-options \
	-cp %{annotation_api} \
	-d classes @sources.list
jar cf jakarta.interceptor-api.jar -C classes .
jar tf jakarta.interceptor-api.jar | grep -E '\.(java|jar|so|node|wasm)$' && exit 1 || true
jar tf jakarta.interceptor-api.jar | grep -F 'javax/interceptor/' && exit 1 || true
jar tf jakarta.interceptor-api.jar | grep -F module-info.class && exit 1 || true
javap -verbose -cp jakarta.interceptor-api.jar jakarta.interceptor.AroundInvoke | grep -F 'major version: 52'

python - << 'PY'
text = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>jakarta.interceptor</groupId>
  <artifactId>jakarta.interceptor-api</artifactId>
  <version>%{version}</version>
  <name>Jakarta Interceptors API</name>
  <description>Jakarta Interceptors API %{version}.</description>
  <url>https://github.com/jakartaee/interceptors</url>
  <licenses>
    <license>
      <name>EPL-2.0 OR GPL-2.0-only WITH Classpath-exception-2.0</name>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>jakarta.annotation</groupId>
      <artifactId>jakarta.annotation-api</artifactId>
      <version>3.0.0</version>
    </dependency>
  </dependencies>
</project>
"""
open("jakarta.interceptor-api.pom", "w", encoding="utf-8").write(text)
PY

%install
sysjar install --buildroot %{buildroot} \
	--artifact jakarta.interceptor-api.pom:jakarta.interceptor-api.jar \
	--file-name jakarta.interceptor-api \
	--filelist .mfiles

%check
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
JAR=%{buildroot}%{_javadir}/jakarta.interceptor-api.jar
test -f "$JAR"
test -f %{annotation_api}
mkdir -p check
cat > check/Smoke.java << 'END'
import jakarta.interceptor.AroundInvoke;
import jakarta.interceptor.InvocationContext;
import java.lang.reflect.Method;
public class Smoke {
	@AroundInvoke
	public Object call(InvocationContext ctx) {
		return null;
	}
	public static void main(String[] args) throws Exception {
		Method method = Smoke.class.getDeclaredMethod("call", InvocationContext.class);
		AroundInvoke mark = method.getAnnotation(AroundInvoke.class);
		if (mark == null) {
			throw new AssertionError("missing");
		}
		System.out.println("interceptor_ok AroundInvoke");
	}
}
END
javac --release 8 -encoding UTF-8 -Xlint:-options \
	-cp "$JAR:%{annotation_api}" \
	-d check check/Smoke.java
java -cp "check:$JAR:%{annotation_api}" Smoke > check/out.txt
cat check/out.txt
grep -F -qx 'interceptor_ok AroundInvoke' check/out.txt

%files -f .mfiles
%license LICENSE.md
%doc README.md NOTICE.md
